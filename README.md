:star2: **All credit goes to Benjamin Bajic for his initial time logging script.** :star2:

# How to run the app

Rename *.jira-env.example* to *.jira-env* and populate it with valid data. Run with `docker compose up --build -d`. Access the app via *localhost:5000*. Data is preserved when tab closes.

> :information_source: Install web page as application (Edge: *More Tools -> Apps -> Install this site as an app*) so you don't have to access it via browser, but just like any other app.

# Capabilities

### General Scratchpad

Write down most common tickets you're working and reviewing right now, write down what others are working on, or whatever you want. 

> :information_source: Scratchpad content is preserved across all time logging submitions and exiting the tab/app  
> :information_source: Scratchpad content is not sent to Jira  

### Time Logging

Date is prefilled to today's date by default. Besides logging time on tickets, there's a textbox below the list of tickets where you can write down notes for that day.

> :information_source: Notes textbox content is saved locally and is not sent to Jira  
> :information_source: Everything that you've written is preserved accross the tab closing and re-opening. Textboxes are emptied out only upon submitting the log for that day (General Scratchpad is an exception, it's never cleared automatically)  
> :information_source: Only date, tickets, their durations and descriptions are sent to Jira  
> :warning: For a certain date, you can log the time only once  

Once the data is filled, click the submit button and data will be sent to Jira. Result of the script execution will be shown below the submit button. 

### View Previous Logs

You can view all the logs and the notes for previously logged days. You can either view the data for a specific day, or last 10 logs.