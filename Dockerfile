FROM ubuntu:18.04

ENV SYNTHETICAPERTURERANDOM_DIR /opt/twitter_bot
ENV HOME /root

COPY requirements ./requirements

RUN apt-get update
RUN apt-get -y install software-properties-common
RUN apt-add-repository universe
RUN apt-get update
RUN apt-get -y install python3-pip

RUN pip3 install -r requirements/requirements.txt

# copy scripts
COPY scripts /usr/bin

RUN mkdir -p $SYNTHETICAPERTURERANDOM_DIR
WORKDIR $SYNTHETICAPERTURERANDOM_DIR
COPY synthetic_aperture_random/ $SYNTHETICAPERTURERANDOM_DIR/synthetic_aperture_random

COPY scripts/ $SYNTHETICAPERTURERANDOM_DIR/scripts

WORKDIR $SYNTHETICAPERTURERANDOM_DIR/synthetic_aperture_random
CMD [ "run" ]
