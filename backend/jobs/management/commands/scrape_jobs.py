import sys
import os
from django.core.management.base import BaseCommand
from jobs.models import Job

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Import the scraper after modifying sys.path
try:
    from completescrap import CombinedDiceJobScraper  # Import the scraper from the project root
except ImportError as e:
    print(f"Error importing completescrap: {e}")
    raise

class Command(BaseCommand):
    help = 'Scrapes job data from Dice.com and stores it in the database'

    def handle(self, *args, **kwargs):
        scraper = CombinedDiceJobScraper()

        # Scraping jobs
        print("Starting to scrape jobs...")
        jobs_data = scraper.scrape_all_jobs()

        # Loop through the scraped jobs and save them to the database
        for job in jobs_data:
            basic_info = job.get('basic_info', {})
            job_id = basic_info.get('title', None)

            if not job_id:
                print("Skipping job: Missing job ID.")
                continue

            # Avoid saving duplicate jobs
            if Job.objects.filter(job_id=job_id).exists():
                print(f"Skipping job {job_id}, already in the database.")
                continue

            # Save the job to the database
            try:
                Job.objects.create(
                    job_id=job_id,
                    title=basic_info.get('title', ''),
                    company_name=basic_info.get('company_name', ''),
                    location=basic_info.get('location', ''),
                    posted_date=basic_info.get('posted_date', ''),
                    salary=job.get('overview', {}).get('salary', ''),
                    work_type=job.get('overview', {}).get('work_type', ''),
                    employment_type=job.get('overview', {}).get('employment_type', ''),
                    skills=', '.join(job.get('skills', [])),
                    description=job.get('job_details', {}).get('Description', ''),
                    # Add other fields if necessary
                )
                print(f"Job {job_id} saved to database.")
            except Exception as e:
                print(f"Error saving job {job_id}: {e}")
