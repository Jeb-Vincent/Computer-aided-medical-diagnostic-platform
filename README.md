# Computer-Aided Medical Diagnostic Platform 

## Introduction

This project is a course design project for "Comprehensive Practice of Artificial Intelligence and Big Data Application Development".

The platform is dedicated to providing clinicians with integrated services for medical image generation, image segmentation, and auxiliary analysis. Addressing pain points such as high costs of multimodal image acquisition and difficulties in postoperative risk assessment in orthopedic surgery, the system integrates **an improved generative adversarial network (ResAPA-CycleGAN)**, **traditional image processing algorithms**, and **a large language model (DeepSeek)**, achieving a complete closed loop from raw image input to diagnostic auxiliary output.

### Core Values

- **Low-cost multimodal imaging**: AI is used to convert monomodal lung CT images into multimodal CTA (CT angiography) images, solving the problems of complex and costly CTA acquisition processes.

- **Postoperative risk assessment**: By precisely segmenting the bone cement area after spinal surgery, doctors can be assisted in assessing the risk of leakage.

- **Healthcare Economics Visualization**: By integrating national medical subsidies and examination fee data, the advantages of cost control can be intuitively demonstrated.

  

## Features

### 1. Image Generation: CT -> CTA 

- **Core Algorithm**: Based on **ResAPA-CycleGAN** (an improved CycleGAN that introduces the ASPP module and the AdaLIN normalization mechanism).
- **Function Description**: Users can upload single-modal lung CT images, and the system will automatically infer and generate corresponding high-quality CTA images.
- **Advantage**: While maintaining anatomical consistency, it significantly improves the texture details and modal features of the images (SSIM index reaches 0.897).

### 2. Image Segmentation: Bone cement area extraction

- **Core Algorithm**: Threshold segmentation algorithm based on the significance of grayscale differences.
- **Function Description**: DICOM format images are analyzed and processed for postoperative spinal surgery, accurately extracting and visually marking the bone cement area.
- **Application scenarios**: Postoperative follow-up examination in orthopedics to assess the risk of bone cement leakage.

### 3. AI Assistant

- **Technical Support**: Integrates the **DeepSeek V11** language model.
- **Function Description**: It supports natural language interaction and provides medical advice, operation instructions, and terminology explanations.
- **Interaction optimization**: Supports streaming dialogue and contextual understanding.

### 4. Data Analysis

- **Technical Implementation**: Python web crawler + ECharts visualization.
- **Function Description**: It captures national medical insurance policies and CT/CTA examination fees from various hospitals, generating pie charts, bar charts, etc., to help doctors and patients understand economic data.

### 5. Medical Science Popularization and Multimedia

- It provides online access to medical science articles and videos to help patients understand basic medical knowledge.

  

## Tech Stack

### Backend

- **Frame**: Django (Python Web Framework)
- **Data processing**: NumPy, Pandas, Pydicom
- **Reptile**: Requests, BeautifulSoup

### Frontend

- **Foundation**: HTML5, CSS3, JavaScript
- **Visualization**: ECharts, Matplotlib

### AI & Algorithms

- **Deep learning framework**: TensorFlow / Keras
- **Large Model Interface**: DeepSeek API 
- **Image Algorithm**: OpenCV, Matplotlib

### Database

- **MySQL**: It stores user information, article/video data, and crawled economic data.

  

## Project Structure

```
Computer-aided-medical-diagnostic-platform/
├── djangoProject/          # Django Project main configuration (settings, urls, wsgi)
├── myapp/                  # Core Application Directory
│   ├── src/                # Algorithm source code storage
│   │   └── home/ubuntu/js/ # This contains the CycleGAN inference script (test_image.py) and model weights.
│   ├── utils/              # Tool script (dicom_processor.py - threshold segmentation)
│   ├── views.py            # View functions 
│   ├── models.py           # Database model (Article, Video, User)
│   └── ...
├── media/                  # Media files
│   └── processed/          # Stores user-uploaded and processed result images
├── templates/              # Front-end HTML pages (homepage, image processing, data analysis, AI chat)
├── static/                 # Static resources (CSS, JS, fonts)
├── CT.py                   # Standalone web crawler script (for scraping medical expense data)
├── manage.py               # Project entrance
└── requirements.txt        # Dependency List
```



## Setup & Usage

### 1. Requirement preparation

Ensure that Python 3.8+ and MySQL database are installed.

```
# Cloning project
git clone [https://github.com/Jeb-Vincent/Computer-aided-medical-diagnostic-platform.git](https://github.com/Jeb-Vincent/Computer-aided-medical-diagnostic-platform.git)
cd Computer-aided-medical-diagnostic-platform

# Install dependencies
pip install -r requirements.txt
```

### 2. Database configuration

Configure the MySQL database connection information in `djangoProject/settings.py` and then execute the migration:

```
python manage.py makemigrations
python manage.py migrate
```

### 3. Model weight preparation

Ensure that the pre-trained weight file (`.hdf5`) of ResAPA-CycleGAN is placed in the `myapp/src/home/ubuntu/js/saved_models/` directory so that the system can load the generator model `G_A2B`.

### 4. Start service

```
python manage.py runserver
```

Access the system via `http://127.0.0.1:8000/`.

