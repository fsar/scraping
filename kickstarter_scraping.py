# Using selenium + phantomJS to get the html code after 
# the JS has run and modified the original html source
from selenium import webdriver
from lxml import html
import re
import pymongo

def get_kickstarter_data(url, pages = 10):
    
    # Initializing dict of REGEX patterns
    regex_patterns = {'id': '"id":(.*?),',
                        'name': '"name":"(.*?)",',
                        'goal': '"goal":(.*?),',
                        'state': '"state":"(.*?)",',
                        'percent funded': '"percent_funded":(.*?)}',
                        'pledged': '"pledged":(.*?),',
                        'pledged usd': '"usd_pledged":"(.*?)",',
                        'blurb': '"blurb":"(.*?)"',
                        'country': '"country":"(.*?)"',
                        'currency': '"currency":"(.*?)"',
                        'staff_pick': '"staff_pick":(.*?),',
                        'deadline': '"deadline":(.*?),',
                        'launched_at': '"launched_at":(.*?),'}
    
    # Initializing list of dicts that will contain the project data
    projects = []
    
    # xpath location of the data-project div attribute
    x_path_p_data = '//div[@class="js-react-proj-card col-full col-sm-12-24 col-lg-8-24"]/@data-project'
    
    # Set the driver with PhantomJS with your own path to the executable
    # More info: http://phantomjs.org/
    driver = webdriver.PhantomJS(executable_path='PATH/phantomjs')
    
    # Looping through Kickstarter's pages
    for pageNo in range (1, pages + 1):
    
        # Retrieve the source and convert it to lxml.html
        print("Scraping data from page: " + str(pageNo))
        print("Url: " + url + str(pageNo))
        driver.get(url + str(pageNo))
        kickstarterHtmlTree = html.fromstring(driver.page_source)
    
        # Storing the data-project div attributes in a list
        page_project_data = [str(item) for item in kickstarterHtmlTree.xpath(x_path_p_data)]
    
        # Parsing the data-project div attribute
        # Storing the parsed data in project dict that will be appended to projects
        for i in range(len(page_project_data)):
            
            project = {}
            for attr_name, pattern in regex_patterns.items():
        
                match = re.search(pattern, page_project_data[i])
                project[attr_name] = match.group(1)
                
            projects.append(project)
            del(project)
    
    # End the driver session
    driver.quit()
    
    # Return the projects
    return projects    
    

def main():
    
    kickstarter_url = "https://www.kickstarter.com/discover/advanced?sort=end_date&page="
    
    # Fetch the data from Kickstarter's website
    projects = get_kickstarter_data(kickstarter_url, 30)
    
    # Connecting to our Mongo DB hosted on mlab.com
    # Set your own URI
    uri = 'mongodb://user:pass@host:port/db'
    client = pymongo.MongoClient(uri)
    db = client.data_scrap
    
    # Lazily creating the collection
    kickstarter_projects = db['kickstarter_projects']

    # Inserting our documents in the collection
    kickstarter_projects.insert_many(projects)
    
    # Retrieve 5 failed projects
    cursor = db.kickstarter_projects.find(filter = {"state":"failed"}, limit = 5)
    
    # Print the results
    print('{} projects are in "failed" state:'.format(cursor.count_documents()))
    for doc in cursor:
        print("Project: {} has failed to raised their goal of {}. Percentage raised: {}"
              .format(doc['id'], doc['goal'], doc['percent funded']))
     
    # Closing the cursor
    cursor.close()

if __name__ == '__main__':
    main()