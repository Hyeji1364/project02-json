from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")
today_date = datetime.now().date()
filename = f"Melonadd/pychart_M_add{current_date}.json"

# 웹 드라이버 설정
options = ChromeOptions()
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
options.add_argument("--headless")
service = ChromeService(executable_path=ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)

# 멜론 웹 페이지에 접속
url = "https://ticket.melon.com/ranking/index.htm"
browser.get(url)
time.sleep(5)  # 페이지 로딩 대기

# "뮤지컬/연극" 버튼 클릭
try:
    concert_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@value='NEW_GENRE_ART']"))
    )
    concert_button.click()
    print("Clicked '뮤지컬/연극' button.")
    time.sleep(3)  # 페이지가 완전히 로드될 때까지 대기
except Exception as e:
    print("Error clicking '뮤지컬/연극' button:", e)

# 페이지 소스 가져오기
page_source = browser.page_source

# BeautifulSoup을 사용하여 HTML 파싱
soup = BeautifulSoup(page_source, 'html.parser')

# 데이터 추출
music_data = []
tracks = soup.select(".tbl.tbl_style02 tbody tr")
for track in tracks[:10]:  # 상위 10개의 트랙만 가져오기
    rank = track.select_one("td.fst .ranking").text.strip()
    change = track.select_one("td.fst .change").text.strip()
    # change 텍스트에서 불필요한 공백 제거
    change = ' '.join(change.split())
    title = track.select_one("div.show_infor p.infor_text a").text.strip()
    place = track.select_one("td:nth-child(4)").text.strip()
    image_url = track.select_one("div.thumb_90x125 img").get('src')
    site_url = "https://ticket.melon.com/ranking/index.htm"

    # 날짜 정보 추출
    date_elements = track.select("ul.show_date li")
    date = " ".join([element.text.strip() for element in date_elements])

    music_data.append({
        "rank": rank,
        "change": change,
        "title": title,
        "Venue": place,
        "ImageURL": image_url,
        "date": date,
        "site": site_url
    })

# 네이버에서 뮤지컬 기본 정보 및 관람평 크롤링
for musical in music_data:
    # 검색어 수정
    search_title = musical['title'].replace('한국어버전', '').strip() if '노트르담 드 파리' in musical['title'] else musical['title']
    search_url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkkw&pkid=269&query={search_title}+기본정보"
    browser.get(search_url)
    time.sleep(5)  # 페이지 로딩 대기

    # 기본정보 추출
    try:
        info_elements = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cm_info_box .info_group dd"))
        )
        
        overview = info_elements[0].text.strip() if len(info_elements) > 0 else "-"
        period = info_elements[1].text.strip() if len(info_elements) > 1 else "-"
        time_info = info_elements[2].text.strip() if len(info_elements) > 2 else "-"
        place = info_elements[3].text.strip() if len(info_elements) > 3 else "-"
        
        # 좌석배치도 링크 추출
        try:
            seat_link_element = browser.find_element(By.XPATH, "//span[@class='line_text']/a[contains(text(), '좌석배치도')]")
            seat_link = seat_link_element.get_attribute('href')
        except Exception as e:
            seat_link = "-"

        # 인스타그램 링크 추출
        try:
            instagram_element = browser.find_element(By.XPATH, "//a[contains(@href, 'instagram.com')]")
            instagram = instagram_element.get_attribute('href')
        except Exception as e:
            instagram = "-"

        musical['overview'] = overview
        musical['period'] = period
        musical['time_info'] = time_info
        musical['place'] = place
        musical['seat_link'] = seat_link
        musical['instagram'] = instagram
        
        # 디버깅 로그 출력
        print(f"Extracted info for {musical['title']}:")
        print(f"  Overview: {overview}")
        print(f"  Period: {period}")
        print(f"  Time info: {time_info}")
        print(f"  Place: {place}")
        print(f"  Seat link: {seat_link}")
        print(f"  Instagram: {instagram}")
        
    except Exception as e:
        print(f"Error extracting '기본정보' for {musical['title']}:", e)
        musical['overview'] = "-"
        musical['period'] = "-"
        musical['time_info'] = "-"
        musical['place'] = "-"
        musical['seat_link'] = "-"
        musical['instagram'] = "-"

    # 관람평 추출
    search_url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkkw&pkid=269&query={musical['title']}+관람평"
    browser.get(search_url)
    time.sleep(5)  # 페이지 로딩 대기

    try:
        # 전체 평점 추출
        try:
            overall_rating_element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".lego_average_star .area_text_box"))
            )
            overall_rating = overall_rating_element.text.strip()
            num_participants_element = browser.find_element(By.CSS_SELECTOR, ".area_participate_text")
            num_participants = num_participants_element.text.strip()
            musical['overall_rating'] = f"{overall_rating} ({num_participants})"
        except Exception as e:
            print(f"Error extracting overall rating for {musical['title']}:", e)
            musical['overall_rating'] = "-"

        # 개별 평점 추출
        reviews = []
        review_elements = browser.find_elements(By.CSS_SELECTOR, ".lego_review_list .area_card")
        for review_element in review_elements:
            try:
                rating = review_element.find_element(By.CSS_SELECTOR, ".area_title_box .area_text_box .blind").text.strip()
                review_text = review_element.find_element(By.CSS_SELECTOR, ".desc._text").text.strip()
                reviewer_id = review_element.find_element(By.CSS_SELECTOR, "dd.this_text_stress").text.strip()
                review_date = review_element.find_element(By.CSS_SELECTOR, "dd.this_text_normal").text.strip()
                reviews.append({
                    "rating": rating,
                    "review_text": review_text,
                    "reviewer_id": reviewer_id,
                    "review_date": review_date
                })
            except Exception as e:
                print(f"Error extracting individual review for {musical['title']}:", e)
                continue
        musical['reviews'] = reviews
    except Exception as e:
        print(f"Error extracting '관람평' for {musical['title']}:", e)
        musical['overall_rating'] = "-"
        musical['reviews'] = []

# 데이터를 JSON 파일로 저장
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(music_data, f, ensure_ascii=False, indent=4)

# 브라우저 종료
browser.quit()
