import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

API_KEY = 'AIzaSyBbL3HZF1RAUlhQ1hxdfqG2UDokPqjPnyE'

st.title("YouTube 数字货币KOL查找工具")

query = st.text_input("请输入关键词（如：数字货币交易、crypto trading等）", "crypto trading")
max_results = st.number_input("最多查找视频数", min_value=1, max_value=50, value=20)
run = st.button("开始查找")

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

def get_video_comment_count(youtube, video_id):
    response = youtube.videos().list(
        part='statistics',
        id=video_id
    ).execute()
    if not response['items']:
        return 0
    return response['items'][0]['statistics'].get('commentCount', 0)

if run:
    st.write("正在查找，请稍候...")
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    videos = search_videos(query, max_results)
    data = []
    seen_channels = set()
    for video in videos:
        channel_id = video['channel_id']
        if channel_id in seen_channels:
            continue
        seen_channels.add(channel_id)
        channel_info = get_channel_info(youtube, channel_id)
        if not channel_info:
            continue
        comment_count = get_video_comment_count(youtube, video['video_id'])
        channel_info['评论数'] = comment_count
        data.append(channel_info)
    if data:
        df = pd.DataFrame(data)
        st.write(f"共找到 {len(df)} 个独立频道")
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载结果为CSV",
            data=csv,
            file_name='youtube_kol.csv',
            mime='text/csv'
        )
    else:
        st.write("未找到相关频道。") 