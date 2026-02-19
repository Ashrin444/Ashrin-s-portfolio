# create virtual environment
RUN python3 -m venv /opt/venv

# activate venv
ENV PATH="/opt/venv/bin:$PATH"

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
RUN pip install -r requirements.txt
