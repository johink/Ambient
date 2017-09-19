import boto3
import os
import time
import generate_model

os.chdir("/home/ubuntu/")

ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')

scraper = ec2.Instance(os.environ["SCRAPERID"])
scraper.start()

if scraper.state['Name'] not in ["pending","running"]:
    print("Error starting instance...")
    print(response)
    raise Exception("Could not start scraper instance")

i = 0
while True:
    time.sleep(60)
    i += 1
    scraper.reload()
    if scraper.state["Name"] in ['stopping','stopped']:
        break
    print("Still scraping after {} minutes".format(i))

print("Scraping finished, running generate_model.py")
generate_model.main()


