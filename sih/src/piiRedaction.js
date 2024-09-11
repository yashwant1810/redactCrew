import React, { useState } from "react";
import axios from "axios";
import "./piiRedaction.css";
import { FaDownload } from 'react-icons/fa';  // Download icon

const PiiRedaction = () => {
  const [files, setFiles] = useState([]);
  const [piiOptions, setPiiOptions] = useState({
    aadhar: true,
    pan: true,
    drivingLicense: true,
    name: true,
  });
  const [processedFiles, setProcessedFiles] = useState([]);

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleToggle = (option) => {
    setPiiOptions({
      ...piiOptions,
      [option]: !piiOptions[option],
    });
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    formData.append("piiOptions", JSON.stringify(piiOptions));

    try {
      const response = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setProcessedFiles(response.data.processedFiles);  // Store the list of processed files
    } catch (error) {
      console.error("Error uploading files", error);
    }
  };

  const handleDownload = (filename) => {
    window.open(`http://127.0.0.1:5000/download/${filename}`, '_blank');
  };

  return (
    <div className="redaction-page">
      <h1>PII Redaction</h1>
      <input type="file" multiple onChange={handleFileChange} />

      <div className="toggle-buttons">
        <label>
          Aadhaar:
          <input
            type="checkbox"
            checked={piiOptions.aadhar}
            onChange={() => handleToggle("aadhar")}
          />
        </label>
        <label>
          PAN:
          <input
            type="checkbox"
            checked={piiOptions.pan}
            onChange={() => handleToggle("pan")}
          />
        </label>
        <label>
          Driving License:
          <input
            type="checkbox"
            checked={piiOptions.drivingLicense}
            onChange={() => handleToggle("drivingLicense")}
          />
        </label>
        <label>
          Name:
          <input
            type="checkbox"
            checked={piiOptions.name}
            onChange={() => handleToggle("name")}
          />
        </label>
      </div>

      <button onClick={handleSubmit}>Submit</button>

      {processedFiles.length > 0 && (
        <div className="processed-files">
          <h2>Processed Files</h2>
          <ul>
            {processedFiles.map((file, index) => (
              <li key={index}>
                {file}{" "}
                <FaDownload
                  className="download-icon"
                  onClick={() => handleDownload(file)}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PiiRedaction;