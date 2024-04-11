import os
import glob
import pandas as pd
import streamlit as st
from datetime import datetime

folder_path = 'C:/Users/leeji/OneDrive/Desktop/fadu/fadu-one/pythonProject/badblock'  # 폴더 경로 설정

def find_changed_elements(prev_df, curr_df):
    # 그룹화 기준 열
    group_columns = ['sn', 'plane', 'mp_block', 'die', 'channel']

    # 이전 파일과 현재 파일 그룹화
    prev_grouped = prev_df.groupby(group_columns)
    curr_grouped = curr_df.groupby(group_columns)

    changed_rows = []

    # 현재 파일에서 그룹별로 확인
    for key, curr_group in curr_grouped:
        if key in prev_grouped.groups:
            prev_group = prev_grouped.get_group(key)

            # pe_cycle 값이 변경된 경우
            changed = curr_group[curr_group['pe_cycle'] != prev_group['pe_cycle'].iloc[0]]
            if not changed.empty:
                changed['status'] = 'change'  # status 열 추가
                changed['prev_pe_cycle'] = prev_group['pe_cycle'].iloc[0]  # 이전 파일의 pe_cycle 값 추가
                changed_rows.append(changed)
        else:
            # 이전 파일에 없는 새로운 데이터
            new_data = curr_group.copy()
            new_data['status'] = 'new'  # status 열 추가
            changed_rows.append(new_data)

    # 이전 파일에만 존재하는 데이터 확인
    for key, prev_group in prev_grouped:
        if key not in curr_grouped.groups:
            deleted_data = prev_group.copy()
            deleted_data['status'] = 'delete'  # status 열 추가
            changed_rows.append(deleted_data)

    if changed_rows:
        result = pd.concat(changed_rows, ignore_index=True)
        return result
    else:
        return pd.DataFrame()


# 폴더 내의 CSV 파일 목록 가져오기
csv_files = glob.glob(os.path.join(folder_path, 'carrera_RDT_raw_TB_*.csv'))
csv_files.sort()  # 파일 이름 기준으로 정렬

# 첫 번째 파일을 이전 데이터로 설정
prev_file = csv_files[0]
prev_df = pd.read_csv(prev_file)

all_changed_df = pd.DataFrame()

# 두 번째 파일부터 이전 파일과 비교
for curr_file in csv_files[1:]:
    curr_df = pd.read_csv(curr_file)

    # 변경된 요소 찾기
    changed_df = find_changed_elements(prev_df, curr_df)

    # 변경된 요소가 있는 경우 concat
    if not changed_df.empty:
        changed_df['file'] = os.path.basename(curr_file)  # 파일명 열 추가
        all_changed_df = pd.concat([all_changed_df, changed_df], ignore_index=True)

    # 현재 파일을 이전 파일로 업데이트
    prev_df = curr_df

# Streamlit 앱 시작
st.title('Changed Elements')

if not all_changed_df.empty:
    # 열 순서 변경
    columns = all_changed_df.columns.tolist()
    if 'pe_cycle' in columns and 'prev_pe_cycle' in columns:
        pe_cycle_index = columns.index('pe_cycle')
        prev_pe_cycle_index = columns.index('prev_pe_cycle')
        columns.pop(prev_pe_cycle_index)
        columns.insert(pe_cycle_index, 'prev_pe_cycle')
        all_changed_df = all_changed_df[columns]

    # 결과 데이터프레임 표시
    st.dataframe(all_changed_df)

    # status 열로 정렬하는 옵션 추가
    sort_option = st.selectbox('Sort by Status', ['', 'change', 'new', 'delete'])
    if sort_option:
        sorted_df = all_changed_df[all_changed_df['status'] == sort_option]
        st.dataframe(sorted_df)

    # 결과 파일 저장
    today = datetime.today().strftime('%Y-%m-%d')
    output_file = f'{folder_path}complete_{today}.csv'
    all_changed_df.to_csv(output_file, index=False)
    st.success(f'Results saved to: {output_file}')
else:
    st.info('No changed, new, or deleted elements found.')