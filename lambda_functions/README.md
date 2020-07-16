# Data Carousel Lambda Functions
We use AWS Lambda functions to glue together the components of the Data 
Carousel. 

## Job Submission
This [function](submitJob.py) is invoked by the API Gateway in response to the POST operation
on the `/jobs` endpoint. It creates a unique Job ID, and creates a record in the
`DataCaorouselJobs` table. It executes the provided query against the 
`BasicFusionFiles` table. That will see which fusion files are to be included
in the job. Based on these results it will create records for each file in the
`DataCaorouselJobFiles` table. The function returns a JSON document providing
the user with the JobID and a count of files that will be included in the
job.

## File Restored from Glacier
This [function](onFileRestored.py) is invoked by S3 as each file is restored 
from Glacier. It looks up jobs that are interested in that file. For each job 
the script will create a work record and add it to that job's work queue.
