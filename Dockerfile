# Use a lightweight base Python image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the Gradio app code into the container
COPY . .

# Install necessary Python packages
RUN pip install gradio
RUN pip install phue

# Command to run when container starts
CMD ["python", "main.py"]