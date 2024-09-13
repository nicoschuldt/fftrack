# FFTrack README

## Description
FFTrack is a Python-based music recognition tool that empowers users to identify songs using audio input. Implementing the Fast Fourier Transform (FFT) for audio processing, it offers a sophisticated yet user-friendly approach to music recognition.

## Features
- **Fast Fourier Transform (FFT)** for advanced audio processing
- **Command line interface (CLI)** for straightforward use
- **Recognition capabilities** for both live audio input and pre-recorded files
- **A simple song information database** for easy storage and retrieval of song data

## Installation
Before installing FFTrack, you need to ensure Python is installed on your system. FFTrack requires **Python 3.6 or later**. You also need **pip** (Python package installer) to install the required packages.

First, clone this repository to your local machine:
```
git clone <repository-url>
```
Navigate into the project directory:
```
cd fftrack
```
Install the required Python packages with:
```
pip install -r requirements.txt
```
To get FFTrack up and running, use the setup file with the following command:
```
python setup.py install
```
After installation, verify if FFTrack is correctly installed by:
```
fftrack --help
```
This should display the available commands in FFTrack.

## Usage

### Database Setup
To set up the database for storing song information, you need to populate it first. For convenience, FFTrack includes a script to automatically download a selection of songs and add them to the database:
```
python -m fftrack.scripts.populate_database
```

### Listening for a Song
To record audio directly through a microphone and identify the song, run:
```
fftrack listen
```

### Identifying a Song from an Audio File
To recognize a song from a pre-recorded audio file, execute:
```
fftrack identify <path_to_audio_file>
```

### Top Matches
To display the top song matches for the queried audio sample, FFTrack aligns and compares the audio fingerprints to its database achieving higher accuracy in song identification.

## Configuration
FFTrack can be configured according to user preference by modifying the `config.json` file in the `fftrack` directory. Available configurations include sampling rate, audio processing parameters, and database settings.

For creating a new configuration file or modifying existing settings, FFTrack provides CLI commands accessible via:
```
fftrack config
```
This feature allows users to tailor FFTrack's performance to specific requirements.

## License
FFTrack is open-source software licensed under the MIT License, ensuring it is free to use, modify, and distribute.

## Contact
For any inquiries or contributions, you can open an issue in the repository or directly contact the developers through their respective GitHub profiles.