# redactCrew

Welcome to **redactCrew**—a cutting-edge tool for detecting and redacting Personally Identifiable Information (PII) from your documents and images. This project was built for the 2024 Smart India Hackathon Grande Finale under the Ministry of Electronics and Information Technology of India. 

The contributors are - 

[Yashwant Balaji](https://github.com/yashwant1810)

[Rohit Kedar](https://github.com/kedarrohit)

[Hrishikesh Virupakshi](https://github.com/hrishiii27)

[Sai Sathwik Matury](https://github.com/wixk7)

[Jasmine Jose](https://github.com/Jasmineimis)

[Dhayanandhan M](https://github.com/dhayeah7)



CHECK OUT THE [NPM PACKAGE](https://www.npmjs.com/package/pii-redactor) & THE [PYTHON PACKAGE](https://pypi.org/project/redactCREW/1.0.0/#files) HERE !!!

## 🚀 Getting Started

### Project Structure

The project is neatly divided into two main components:

- **`flask-backend`**: The server-side application responsible for handling file uploads, PII detection, and redaction.
- **`sih`**: The client-side React application offering an intuitive interface for users to interact with the PII redaction features.
- **`pii-redactor-tool`**: The python package comprising of the scripts running to achieve the functionalities of the project.
  
### Frontend (React)

The frontend provides a modern, dynamic user experience with:

- **React**: The core library for building the user interface.
- **Axios**: For making smooth HTTP requests to the backend.
- **React Icons**: A set of icons to enhance the UI, including download and spinner icons.
- **React Router DOM**: For seamless navigation between pages.
- **Tailwind CSS**: For styling and creating a responsive design.

### Backend (Flask)

The backend handles the heavy lifting with:

- **Flask**: The web framework powering the API.
- **Flask-CORS**: To handle cross-origin requests.
- **Werkzeug**: Utility functions for secure file handling.
- **PyMuPDF**: For processing PDF documents.
- **pytesseract**: To perform Optical Character Recognition (OCR) on images.
- **Pillow**: For image processing.
- **OpenCV**: For advanced image manipulation.
- **google-generativeai**: To detect PII using the Gemini API.
- **NumPy**: For numerical operations and data processing.
- **FuzzyWuzzy**: For fuzzy matching of text.

### npm Package

To streamline integration into your workflow, `redactCrew` also offers an npm package. This package provides a simple API for integrating PII detection and redaction features into your own projects. You can install and use the package with: 

```bash
npm i sih_package
```

## 📦 Installation

### Prerequisites

Ensure you have the following installed:

- Python 3.x
- Node.js and npm

### Step-by-Step Setup

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yashwant1810/redactCrew.git
   cd redactCrew
   ```

2. **Backend Setup**:

   Navigate to the `flask-backend` directory and install the Python dependencies:

   ```bash
   cd flask-backend
   pip3 install flask flask-cors werkzeug PyMuPDF pytesseract Pillow opencv-python google-generativeai numpy fuzzywuzzy
   ```

   Create a `.env` file in the `flask-backend` directory for your environment variables.

3. **Frontend Setup**:

   Move to the `sih` directory and install the necessary npm packages:

   ```bash
   cd ../sih
   npm install react axios react-icons react-router-dom tailwindcss
   ```

4. **Running the Application**:

   - **Start the Flask Backend**:

     ```bash
     cd flask-backend
     python3 app.py
     ```

   - **Start the React Frontend**:

     ```bash
     cd ../sih
     npm start
     ```

   Your React app will be live at `http://localhost:3000`, and the Flask API will be accessible at `http://localhost:5000`.

## 🛠️ Usage

1. **Upload**: Drag and drop or select a file to upload through the React interface.
2. **Configure**: Choose the types of PII you want to detect and redact.
3. **Download**: Receive and download the redacted file once processing is complete.

## 🤝 Contributing

We welcome contributions to improve `redactCrew`! Feel free to:

- Open issues for bugs or feature requests.
- Submit pull requests with enhancements or fixes.

Please ensure your contributions follow our coding standards and include tests where applicable.

## 📜 License

`redactCrew` is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
