import requests
import re
import pandas as pd
import time

HEADERS = {
    'Accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
MAIN_LINK = 'https://www.detmir.ru/catalog/index/name/baby_food_milk/'

# %%
def get_last_page_number(url):

  response = requests.get(url, headers=HEADERS, verify=False, timeout=4)
  html_text = response.text

  pattern_main = r'data-testid="pager_item_right_spread".*?<span class="\w+">(.*?)</span></span></span></div></li></ol></nav></div>'
  pattern_second = r'\d{3}'
  
  match = re.search(pattern_main, html_text, re.DOTALL)
  num = re.search(pattern_second, match.group(1), re.DOTALL).group(0)
  
  return(int(num))
# %%
def extract_substrings(text, anchor="productPrice", length=1240):
    pattern = re.compile(f"{re.escape(anchor)}(.{{{length}}})")
    return pattern.findall(text)
# %%
def extract_product_url(text):
    match = re.search(r'href="([^"]+)"', text)
    return match.group(1) if match else None
# %%
def extract_product_id(text):
    match = re.search(r'index\/id\/(\d*)\/', text)
    return match.group(1) if match else None
# %%
def extract_product_name(text):
    match = re.search(r'<a href=\"[^\"]+?\"[^>]*?>\s*<span[^>]*?>(.*?)</span>', text)
    return match.group(1).strip() if match else None
# %%
def extract_prices(text):
    matches = re.findall(r'(\d[\d \s]*,?\d*)\s?₽', text)

    def clean_to_float(val):
        cleaned = val.replace(' ', '').replace(' ', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
        
    if len(matches) >= 2:
        return clean_to_float(matches[0]), clean_to_float(matches[1])
    elif len(matches) == 1:
        return clean_to_float(matches[0]), None
    else:
        return None, None
# %%
links = []
for page in range(1,get_last_page_number(MAIN_LINK)+1):
# for page in range(1,15):
  url = f"https://www.detmir.ru/catalog/index/name/baby_food_milk/?page={page}"
  links.append(url)

substrings = []
for link in links:
    try:
        response_text = requests.get(link, headers=HEADERS, verify=False, timeout=4).text
        substrings.extend(extract_substrings(response_text))
        print("-----------------------------------------\n" + link + "\n")
    except Exception as e:
        print(f"Ошибка при обработке {link}: {e}")
    time.sleep(15)

# %%
df = pd.DataFrame({
    "substring": substrings
})

df["product_id"] = df["substring"].apply(extract_product_id)
df["product_url"] = df["substring"].apply(extract_product_url)
df["product_name"] = df["substring"].apply(extract_product_name)

test_string = "Цена от 60,70 ₽ до 75,90 ₽"
assert extract_prices(test_string) == (60.70, 75.90)

df[["price_1", "price_2"]] = df["substring"].apply(lambda x: pd.Series(extract_prices(x)))

# print(df[["product_url","price_1", "price_2"]])
# print(df)
df.to_csv("output.txt", sep="\t", float_format="%.2f", index=False)
print("done")