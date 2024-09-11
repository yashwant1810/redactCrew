import React, { useState } from "react";
import axios from "axios";
import "./piiRedaction.css";
import { FaDownload, FaSpinner } from "react-icons/fa"; // Added spinner icon

const PiiRedaction = () => {
  const [files, setFiles] = useState([]);
  const [piiOptions, setPiiOptions] = useState({
    aadhar: true,
    pan: true,
    drivingLicense: true,
    name: true,
  });
  const [processedFiles, setProcessedFiles] = useState([]);
  const [loading, setLoading] = useState(false); // State for loading

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    formData.append("piiOptions", JSON.stringify(piiOptions));

    setLoading(true); // Set loading to true when the form is submitted

    try {
      const response = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setProcessedFiles(response.data.processedFiles);  // Store the list of processed files
    } catch (error) {
      console.error("Error uploading files", error);
    } finally {
      setLoading(false); // Set loading to false when the processing is done
    }
  };

  const handleDownload = (filename) => {
    window.open(`http://127.0.0.1:5000/download/${filename}`, "_blank");
  };

  return (
    <div className="redaction-page">
      <h1>PII Redaction</h1>
      <input type="file" multiple onChange={handleFileChange} />

      <button className="submit-btn" onClick={handleSubmit} disabled={loading}>
        Submit
      </button>

      {loading && (
        <div className="loading-icon">
          <FaSpinner className="fa-spin" /> {/* Rotating loading icon */}
        </div>
      )}

      {!loading && processedFiles.length > 0 && (
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