import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import os
import io

API_KEY = 'AIzaSyBbL3HZF1RAUlhQ1hxdfqG2UDokPqjPnyE'
CHECKED_FILE = "checked_channels.txt"

st.title("Youtuber Finder")

query = st.text_input("请输入关键词（如：数字货币交易、crypto trading等）", "crypto trading")
max_results = st.number_input("最多查找视频数", min_value=1, max_value=200, value=200)
min_subs = st.number_input("最小订阅数", min_value=0, value=0)
max_subs = st.number_input("最大订阅数", min_value=0, value=100000000)
min_views = st.number_input("最小播放量", min_value=0, value=0)
max_views = st.number_input("最大播放量", min_value=0, value=1000000000)
run = st.button("开始查找")

def load_checked_channels():
    if not os.path.exists(CHECKED_FILE):
        return set()
    with open(CHECKED_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_checked_channels(new_channels):
    checked = load_checked_channels()
    with open(CHECKED_FILE, "a") as f:
        for cid in new_channels:
            if cid not in checked:
                f.write(cid + "\n")

def search_videos(query, total_results):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    videos = []
    next_page_token = None
    fetched = 0
    while fetched < total_results:
        max_results = min(50, total_results - fetched)
        search_response = youtube.search().list(
            q=query,
            type='video',
            part='id,snippet',
            maxResults=max_results,
            pageToken=next_page_token
        ).execute()
        for item in search_response['items']:
            videos.append({
                'video_id': item['id']['videoId'],
                'channel_id': item['snippet']['channelId']
            })
        fetched += len(search_response['items'])
        next_page_token = search_response.get('nextPageToken')
        if not next_page_token:
            break
    return videos

def get_channel_info(youtube, channel_id):
    response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    ).execute()
    if not response['items']:
        return None
    item = response['items'][0]
    return {
        '频道名': item['snippet']['title'],
        '频道链接': f"https://www.youtube.com/channel/{channel_id}",
        '订阅数': item['statistics'].get('subscriberCount', 'N/A'),
        '邮箱/关于页': f"https://www.youtube.com/channel/{channel_id}/about"
    }

def get_video_comment_count_and_views(youtube, video_id):
    response = youtube.videos().list(
        part='statistics',
        id=video_id
    ).execute()
    if not response['items']:
        return 0, 0
    stats = response['items'][0]['statistics']
    comment_count = stats.get('commentCount', 0)
    view_count = stats.get('viewCount', 0)
    return comment_count, view_count

if run:
    st.write("正在查找，请稍候...")
    checked_channels = load_checked_channels()
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    videos = search_videos(query, max_results)
    data = []
    seen_channels = set()
    new_channels = set()
    for video in videos:
        channel_id = video['channel_id']
        if channel_id in seen_channels or channel_id in checked_channels:
            continue
        seen_channels.add(channel_id)
        new_channels.add(channel_id)
        channel_info = get_channel_info(youtube, channel_id)
        if not channel_info:
            continue
        comment_count, view_count = get_video_comment_count_and_views(youtube, video['video_id'])
        channel_info['评论数'] = comment_count
        channel_info['视频评论数'] = comment_count
        channel_info['播放量'] = view_count
        data.append(channel_info)
    save_checked_channels(new_channels)
    if data:
        df = pd.DataFrame(data)
        # 只保留订阅数为数字的行
        df = df[df['订阅数'].apply(lambda x: str(x).isdigit())]
        df['订阅数'] = df['订阅数'].astype(int)
        # 只保留播放量为数字的行
        df = df[df['播放量'].apply(lambda x: str(x).isdigit())]
        df['播放量'] = df['播放量'].astype(int)
        # 按订阅数区间过滤
        df = df[(df['订阅数'] >= min_subs) & (df['订阅数'] <= max_subs)]
        # 按播放量区间过滤
        df = df[(df['播放量'] >= min_views) & (df['播放量'] <= max_views)]
        st.write(f"共找到 {len(df)} 个独立频道")
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载结果为CSV",
            data=csv,
            file_name='youtube_kol.csv',
            mime='text/csv'
        )
        # 增加Excel导出功能
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        st.download_button(
            label="下载结果为Excel",
            data=excel_buffer.getvalue(),
            file_name='youtube_kol.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("未找到相关频道。") 