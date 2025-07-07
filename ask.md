We are building a simple tool to generate downloadable trip analytics from the data uploaded by the user. 

Data has to have these columns at minimum: 

For Each Ping;
Lat, 
Long, 
Ping Timestamp

The user will upload a csv with these columns. (On the UI tell the user exact column names they need to have in the CSV to upload)

The system will then calculate the following data points and generate a PDF report in the required format. 


Trip ID, Date of Journey --> directly from trip data
For each ping:
Ping Number
Lat - Long
Distance
Duration b/w the pings
Average Speed
Overall, Optional : Distance Covered, Running Time, Average Speed

The user can either upload one file for all the trips or can upload one file with one trip's data at a time and generate the output PDF file and download it.

Even if the user uploads data of multiple trips in one file, we need to generate the PDF reports individually, one file per trip's data. 

Use the square root formula to calculate distances between each ping. Use timestamp to find the duration between each ping and divide distance & time to calculate the speed. 

Output PDF should look like the one shown in the image, should be PDF, should contain the freight tiger logo as well. 

Use Python, Flask, & Simple React for Frontend.