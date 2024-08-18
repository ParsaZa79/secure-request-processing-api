   # Use an official Python runtime as a parent image
   FROM python:3.12.4-slim

   # Set the working directory in the container
   WORKDIR /app

   # Copy only the requirements file first
   COPY requirements.txt .

   # Install any needed packages specified in requirements.txt
   RUN pip install --no-cache-dir -r requirements.txt

   # Now copy the rest of the application's code
   COPY . .

   # Copy SSL certificate and key
   COPY cert.pem /app/cert.pem
   COPY key.pem /app/key.pem

   # Make port 443 available to the world outside this container
   EXPOSE 443

   # Define environment variables
   ENV FLASK_APP=run.py
   ENV FLASK_ENV=production

   # Create a shell script to run migrations and start the app
   RUN echo '#!/bin/sh\n\
   if [ ! -d "/app/instance" ] || [ ! "$(ls -A /app/instance/*.db 2>/dev/null)" ]; then\n\
       flask db init\n\
       flask db migrate\n\
   fi\n\
   flask db upgrade\n\
   exec gunicorn --certfile=/app/cert.pem --keyfile=/app/key.pem --bind 0.0.0.0:443 run:app\n'\
   > /app/start.sh && chmod +x /app/start.sh

   # Run the shell script when the container launches
   CMD ["/app/start.sh"]