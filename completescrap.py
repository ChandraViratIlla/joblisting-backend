from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
import random
import os

class CombinedDiceJobScraper:
    def __init__(self, headless=True):
        # Selenium setup
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
            self.chrome_options.add_argument('--disable-gpu')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # BeautifulSoup setup
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def modify_url_parameters(self, url, page, page_size):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params['page'] = [str(page)]
        query_params['pageSize'] = [str(page_size)]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))

    def get_job_ids(self, url, page=1, page_size=20):
        """Get job IDs from the search results page"""
        paginated_url = self.modify_url_parameters(url, page, page_size)
        print(f"Fetching search results from: {paginated_url}")
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(paginated_url)
            time.sleep(2)
            
            wait = WebDriverWait(driver, 10)
            cards = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "dhi-search-card")))
            
            job_ids = []
            for card in cards:
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, "a[data-cy='card-title-link']")
                    link_id = title_element.get_attribute('id')
                    if link_id:
                        job_ids.append(link_id)
                except Exception as e:
                    print(f"Error extracting job ID: {e}")
                    continue
            
            # Get total pages
            try:
                pagination = driver.find_elements(By.CSS_SELECTOR, "[data-cy='page-number-link']")
                total_pages = max([int(elem.text) for elem in pagination if elem.text.isdigit()], default=5)
            except Exception:
                total_pages = 5
            
            return job_ids, total_pages
            
        except Exception as e:
            print(f"Error during job ID scraping: {e}")
            return [], 5
        
        finally:
            driver.quit()

    def get_job_details(self, job_id):
        """Get detailed job information using BeautifulSoup"""
        url = f"https://www.dice.com/job-detail/{job_id}"
        print(f"Fetching job details from: {url}")
        
        try:
            # Add random delay between requests
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_data = {
                "job_id": job_id,
                "basic_info": {},
                "overview": {},
                "skills": [],
                "job_details": {},
                "metadata": {}
            }
            
            # Extract basic information
            try:
                job_data["basic_info"]["title"] = soup.find("h1", {"data-cy": "jobTitle"}).get_text(strip=True)
                job_data["basic_info"]["company_name"] = soup.find("a", {"data-cy": "companyNameLink"}).get_text(strip=True)
                job_data["basic_info"]["location"] = soup.find("li", {"data-cy": "location"}).get_text(strip=True)
                job_data["basic_info"]["posted_date"] = soup.find("li", {"data-cy": "postedDate"}).get_text(strip=True)
            except AttributeError as e:
                print(f"Error extracting basic information for job {job_id}: {str(e)}")

            # Extract overview information
            overview_section = soup.find("div", class_="job-overview_jobDetails__kBakg")
            if overview_section:
                for detail in overview_section.find_all("div", class_="job-overview_detailContainer__TpXMD"):
                    chips = detail.find_all("div", class_="chip_chip__cYJs6")
                    for chip in chips:
                        text = chip.get_text(strip=True)
                        if "USD" in text:
                            job_data["overview"]["salary"] = text
                        elif "On Site" in text or "Remote" in text:
                            job_data["overview"]["work_type"] = text
                        elif "Time" in text:
                            job_data["overview"]["employment_type"] = text

            # Extract skills
            skills_section = soup.find("div", {"data-cy": "skillsList"})
            if skills_section:
                for skill in skills_section.find_all("div", class_="chip_chip__cYJs6"):
                    skill_text = skill.get_text(strip=True)
                    if skill_text.startswith("skillChip: "):
                        skill_text = skill_text.replace("skillChip: ", "")
                    job_data["skills"].append(skill_text)


            # Extract job description and requirements with improved section handling
            job_description_div = soup.find("div", {"data-testid": "jobDescriptionHtml"})
            if job_description_div:
                # Initialize current section
                current_section = "Description"
                description_text = []
                
                # Process all children elements sequentially
                for element in job_description_div.children:
                    if element.name == 'b':
                        # New section started
                        section_title = element.get_text(strip=True)
                        if section_title:  # Only create new section if title is not empty
                            current_section = section_title
                            if current_section not in job_data["job_details"]:
                                job_data["job_details"][current_section] = []
                    
                    elif element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:  # Only add non-empty text
                            if current_section in job_data["job_details"]:
                                job_data["job_details"][current_section].append(text)
                            else:
                                description_text.append(text)
                    
                    elif element.name == 'ul':
                        list_items = [li.get_text(strip=True) for li in element.find_all('li')]
                        if list_items:  # Only add non-empty lists
                            if current_section in job_data["job_details"]:
                                job_data["job_details"][current_section].extend(list_items)
                            else:
                                description_text.extend(list_items)
                    
                    elif element.name == 'br':
                        continue
                    
                    elif isinstance(element, str) and element.strip():
                        # Handle any direct text nodes
                        if current_section in job_data["job_details"]:
                            job_data["job_details"][current_section].append(element.strip())
                        else:
                            description_text.append(element.strip())
                
                # Add any remaining description text
                if description_text:
                    if "Description" not in job_data["job_details"]:
                        job_data["job_details"]["Description"] = []
                    job_data["job_details"]["Description"].extend(description_text)

           
            # Extract metadata
            try:
                metadata_section = soup.find("ul", class_="legalInfo")
                if metadata_section:
                    for item in metadata_section.find_all("li", class_="legalInfo"):
                        text = item.get_text(strip=True)
                        if "Dice Id:" in text:
                            job_data["metadata"]["dice_id"] = text.replace("Dice Id:", "").strip()
                        elif "Position Id:" in text:
                            job_data["metadata"]["position_id"] = text.replace("Position Id:", "").strip()
            except AttributeError:
                pass

            return job_data

            
        except Exception as e:
            print(f"Error fetching job details for job ID {job_id}: {e}")
            return None

    def load_existing_jobs(self, output_file):
        """Load existing jobs from JSON file if it exists"""
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading existing jobs: {e}")
        return []

    def save_jobs_to_json(self, jobs, output_file):
        """Save jobs to JSON file with proper formatting"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved {len(jobs)} jobs to {output_file}")
        except Exception as e:
            print(f"Error saving jobs to JSON: {e}")

    def get_scraped_job_ids(self, jobs):
        """Get set of already scraped job IDs"""
        return {job['job_id'] for job in jobs if 'job_id' in job}

    def scrape_all_jobs(self, output_file="dice_jobs.json"):
        """Main function to scrape all jobs with improved data persistence"""
        # Load existing jobs if any
        all_jobs_data = self.load_existing_jobs(output_file)
        scraped_ids = self.get_scraped_job_ids(all_jobs_data)
        print(f"Loaded {len(all_jobs_data)} existing jobs")

        base_url = "https://www.dice.com/jobs"
        search_params = {
            'q': 'python',
            'location': 'United States',
            'latitude': '38.7945952',
            'longitude': '-106.5348379',
            'countryCode': 'US',
            'locationPrecision': 'Country',
            'radius': '30',
            'radiusUnit': 'mi',
            'filters.postedDate': 'ONE',
            'filters.employmentType': 'FULLTIME',
            'language': 'en'
        }
        
        query_string = urlencode(search_params)
        url = f"{base_url}?{query_string}"
        
        current_page = 1
        
        while True:
            # Get job IDs from search results page
            job_ids, total_pages = self.get_job_ids(url, current_page)
            
            print(f"\nProcessing page {current_page} of {total_pages}")
            print(f"Found {len(job_ids)} jobs on this page")
            
            # Track new jobs found on this page
            new_jobs_count = 0
            
            # Get detailed information for each job
            for job_id in job_ids:
                # Skip already scraped jobs
                if job_id in scraped_ids:
                    print(f"Skipping already scraped job ID: {job_id}")
                    continue
                
                job_data = self.get_job_details(job_id)
                if job_data:
                    all_jobs_data.append(job_data)
                    scraped_ids.add(job_id)
                    new_jobs_count += 1
                    print(f"Successfully scraped job: {job_data['basic_info'].get('title', 'Unknown Title')}")
                    
                    # Save progress after each job
                    self.save_jobs_to_json(all_jobs_data, output_file)
            
            print(f"\nFound {new_jobs_count} new jobs on page {current_page}")
            print(f"Total jobs collected so far: {len(all_jobs_data)}")
            
            if current_page >= total_pages:
                print("\nReached last page.")
                break
                
            user_input = input(f"\nCurrent page: {current_page}/{total_pages}\n"
                             f"Enter 'n' for next page, 'p' for previous page, "
                             f"a page number, or 'q' to quit: ").lower()
            
            if user_input == 'q':
                break
            elif user_input == 'n' and current_page < total_pages:
                current_page += 1
            elif user_input == 'p' and current_page > 1:
                current_page -= 1
            elif user_input.isdigit():
                page_num = int(user_input)
                if 1 <= page_num <= total_pages:
                    current_page = page_num
                else:
                    print(f"Invalid page number. Please enter a number between 1 and {total_pages}")
            else:
                print("Invalid input. Please try again.")
        
        # Final save
        self.save_jobs_to_json(all_jobs_data, output_file)
        print(f"\nScraping completed. Total jobs collected: {len(all_jobs_data)}")
        return all_jobs_data

if __name__ == "__main__":
    scraper = CombinedDiceJobScraper()
    jobs_data = scraper.scrape_all_jobs()