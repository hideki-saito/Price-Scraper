import re

import requests
from bs4 import BeautifulSoup

infile = 'infile'
host = "http://www.marksandspencer.com"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/s537.36'}
s = requests.session()

def output_content(text):
    f = open('content.txt', 'w')
    f.write(text)
    f.close()

def get_from_txtfile(filepath):
    f = open(filepath)
    lines = f.readlines()
    f.close()

    return [line.replace("\n", "") for line in lines]

def get_item_urls(url):
    r = s.get(url, headers=headers)
    soup = BeautifulSoup(r.content)
    item_count = soup.find('span', class_="count").text.strip()

    item_urls = []
    page = 0
    while 1:
        page = page + 1
        page_url = url + "?pageChoice=" + str(page)
        r = s.get(page_url,headers=headers)
        soup = BeautifulSoup(r.content)
        item_tags = soup.find_all("a", class_='prodAnchor')
        if len(item_tags) == 0:
            break
        for item_tag in item_tags:
            item_urls.append(item_tag.get('href'))
    return item_urls

def get_data_from_index(text, index):
    var_index = index
    while 1:
        var_index = var_index + 1
        if (text[var_index]) == "<":
            break

    raw_data = text[index:var_index]

    data = re.findall('\d+', raw_data)[0]
    return data

def get_txt_from_index(text, index):
    var_index = index
    while 1:
        var_index = var_index + 1
        if (text[var_index]) == ">":
            start = var_index
        if (text[var_index] == "<"):
            end = var_index
            break
    return text[start+1:end]

def product_review_scraper(url):
    r = s.get(host+url, headers=headers)
    soup = BeautifulSoup(r.content)
    product_name = soup.find(name="h1", attrs={'itemprop':'name'}).text.strip().encode('utf8')
    product_code = soup.find(name="p", attrs={'class': 'code'}).text.strip().encode('utf8')

    product_id = url.split("?")[0].split("/")[-1].upper()
    review_url = "http://marksandspencer.ugc.bazaarvoice.com/2050-en_gb/" + product_id+ "/reviews.djs?format=embeddedhtml"
    response_text = s.get(review_url, headers=headers).content

    flag_review_count = "BVRRRatingSummaryHeaderCounterValue"
    review_count_index = response_text.find(flag_review_count)
    if review_count_index > 0:
        review_count = int(get_data_from_index(response_text, review_count_index))
    else:
        review_count = 0


    reviews = []
    if review_count > 0:
        pageNo = 0
        while len(reviews) < review_count:
            pageNo = pageNo + 1
            page_reviewUrl = review_url + "&page=" + str(pageNo)
            print page_reviewUrl
            response_text = s.get(page_reviewUrl, headers=headers).content
            flag_reviewer = "BVRRNickname"
            reviewer_indexes = [m.start() for m in re.finditer(flag_reviewer, response_text)]

            for i in range(len(reviewer_indexes)):
                review = [product_name, product_code]
                if i == len(reviewer_indexes) -1 :
                    reviewer_text = response_text[reviewer_indexes[i]:]
                else:
                    reviewer_text = response_text[reviewer_indexes[i]:reviewer_indexes[i+1]]
                reviewer_text = reviewer_text.replace("\\", "")

                flag_score = "BVRRRatingNumber"
                score_indexes = [m.end() for m in re.finditer(flag_score, reviewer_text)]
                score = []
                for score_index in score_indexes:
                    score.append(get_data_from_index(reviewer_text, score_index))
                if len(score) < 5:
                    score.extend(['']*(5-len(score)))

                review.extend(score)

                flag_howSize = "BVRRSliderTextDisplayValue"
                howSize_index = reviewer_text.find(flag_howSize)
                if howSize_index > 0:
                    index = howSize_index + len(flag_howSize)
                    how_size = ""
                    while 1:
                        if reviewer_text[index] == '"':
                            break
                        how_size = how_size + reviewer_text[index]
                        index = index + 1
                else:
                    how_size = ""
                review.append(how_size)

                string_flags = ['span class="BVRRReviewText"', 'BVRRValue BVRRReviewTitle', 'BVRRValue BVRRReviewDate', 'BVRRValue BVRRContextDataValue BVRRContextDataValueAge', "BVRRValue BVRRUserLocation"]
                for string_flag in string_flags:
                    string_index = reviewer_text.find(string_flag)
                    if string_index > 0:
                        reviewString = get_txt_from_index(reviewer_text, string_index)
                    else:
                        reviewString = ""
                    review.append(reviewString)
                #print review
                reviews.append(review)
    else:
        review = [product_name, product_code]
        reviews.append(review)

    return reviews
def main():
    #url = "/double-face-blanket-coat-with-wool/p/p22395520?prevPage=plp"
    #url = "/hooded-parka-with-stormwear/p/p22459571?prevPage=plp"

    total_reviews = [['Production Name', 'Production Code', 'OverallScore', 'Quality', 'ValueForMoney', 'Fit', 'Style', 'HowDoesItFit','ReviewText', 'ReviewTitle', 'ReviewDate', 'ReviewerAge', 'ReviewerFrom']]

    infile = raw_input("Please input path of infile")
    category_urls = get_from_txtfile(infile)
    for category_url in category_urls:
        k = 1
        item_urls = get_item_urls(category_url)
        print len(item_urls)
        for item_url in item_urls:
            reviews = product_review_scraper(item_url)
            total_reviews.extend(reviews)
            print item_url

    import csv

    with open("output.csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(total_reviews)

    from os import path
    outfile_path = path.join(path.dirname(path.realpath(__file__)), "output.csv")
    print "Outfile: ", outfile_path

if __name__ == "__main__":
    main()