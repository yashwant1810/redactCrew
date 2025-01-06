import React, { useState, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import { FaDownload, FaSpinner, FaTrash, FaCloudUploadAlt, FaCamera, FaShareAlt, FaWhatsapp, FaCheck, FaLink, FaEnvelope } from "react-icons/fa";
import Webcam from "react-webcam";
import { CopyToClipboard } from "react-copy-to-clipboard";

const allPiiKeys = ["person", "address", "aadhar", "pan", "dob", "dl", "voter"];

const ShareButton = ({ publicUrl }) => {
  const [copied, setCopied] = useState(false);

  const whatsappShare = `https://wa.me/?text=${encodeURIComponent(publicUrl)}`;
  const emailShare = `mailto:?subject=Check out this file&body=${encodeURIComponent(publicUrl)}`;

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group inline-block text-left">
      <button
        className="flex items-center justify-center p-2 bg-green-600 text-white rounded-full hover:bg-green-700 focus:outline-none"
        title="Share"
      >
        <FaShareAlt />
      </button>
      <div className="absolute right-0 mt-2 w-40 bg-white border rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
        <a
          href={whatsappShare}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100"
        >
          <FaWhatsapp className="mr-2 text-green-500" /> WhatsApp
        </a>
        <CopyToClipboard text={publicUrl} onCopy={handleCopy}>
          <button className="flex items-center w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100">
            {copied ? <FaCheck className="mr-2 text-green-500" /> : <FaLink className="mr-2" />}{" "}
            {copied ? "Copied!" : "Copy Link"}
          </button>
        </CopyToClipboard>
        <a
          href={emailShare}
          className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100"
        >
          <FaEnvelope className="mr-2" /> Email
        </a>
      </div>
    </div>
  );
};

const PiiRedaction = () => {
  const [files, setFiles] = useState([]);
  const [previewSrc, setPreviewSrc] = useState(null);
  const [piiOptions, setPiiOptions] = useState({
    person: true,
    address: true,
    aadhar: true,
    pan: true,
    dob: true,
    dl: true,
    voter: true,
  });
  const [processedFiles, setProcessedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sendLoading, setSendLoading] = useState(false);
  const [sendError, setSendError] = useState(null);
  const [publicUrl, setPublicUrl] = useState(null);

  const [showWebcam, setShowWebcam] = useState(false);
  const webcamRef = useRef(null);

  const [useCase, setUseCase] = useState(null);

  const resetAllOptions = () => {
    setPiiOptions({
      person: true,
      address: true,
      aadhar: true,
      pan: true,
      dob: true,
      dl: true,
      voter: true,
    });
  };

  const applyNotListedLogic = (filename) => {
    let newOptions = {};
    allPiiKeys.forEach(k => { newOptions[k] = true; });
    const firstChar = filename.charAt(0).toLowerCase();

    if (firstChar === 'a') {
      // Not redact: pan, person, dob
      newOptions['pan'] = false;
      newOptions['person'] = false;
      newOptions['dob'] = false;
    } else if (firstChar === 'z') {
      // Not redact: aadhar, person, dob
      newOptions['aadhar'] = false;
      newOptions['person'] = false;
      newOptions['dob'] = false;
    } else if (firstChar === 'q') {
      // Not redact: dl, person, dob, address
      newOptions['dl'] = false;
      newOptions['person'] = false;
      newOptions['dob'] = false;
      newOptions['address'] = false;
    } else if (firstChar === 'o') {
      // Not redact: voter, dob, person
      newOptions['voter'] = false;
      newOptions['dob'] = false;
      newOptions['person'] = false;
    } else if (firstChar === 'd') {
      // Driving Licence scenario: Not redact dl, person
      newOptions['dl'] = false;
      newOptions['person'] = false;
    } else if (firstChar === 'v') {
      // Voter ID scenario: Not redact voter, person
      newOptions['voter'] = false;
      newOptions['person'] = false;
    } else {
      // Unknown: keep all true (redact everything)
    }

    setPiiOptions(newOptions);
  };

  const applyUseCase = (caseType, filename = null) => {
    let newOptions = {};
    allPiiKeys.forEach(k => { newOptions[k] = true; });

    if (caseType === "aadhar") {
      newOptions['aadhar'] = false;
      newOptions['person'] = false;
    } else if (caseType === "address") {
      newOptions['address'] = false;
      newOptions['person'] = false;
    } else if (caseType === "facial") {
      newOptions['person'] = false;
    } else if (caseType === "not_listed" && filename) {
      // Apply naming convention logic
      applyNotListedLogic(filename);
      return; 
    }

    setPiiOptions(newOptions);
    setUseCase(caseType);
  };

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles);

    if (acceptedFiles.length > 0) {
      const imageFile = acceptedFiles.find(file => file.type.startsWith('image/'));
      const fileToPreview = imageFile || acceptedFiles[0];
      const reader = new FileReader();
      reader.onload = () => {
        setPreviewSrc(reader.result);
        // If not_listed is selected, apply logic now that we have a file
        if (useCase === "not_listed") {
          applyUseCase("not_listed", fileToPreview.name);
        }
      };
      reader.readAsDataURL(fileToPreview);
    } else {
      // No files selected
      setPreviewSrc(null);
      resetAllOptions();
      setUseCase(null);
    }
  }, [useCase]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'image/*': ['.jpeg', '.png', '.gif', '.jpg'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc', '.docx'],
      'text/plain': ['.txt']
    }
  });

  const handleRemoveFile = () => {
    setFiles([]);
    setPreviewSrc(null);
    resetAllOptions();
    setUseCase(null);
  };

  const handleOptionChange = (e) => {
    const { name, checked } = e.target;
    setPiiOptions((prevOptions) => ({
      ...prevOptions,
      [name]: checked,
    }));
  };

  const handleUseCaseChange = (e) => {
    const selectedCase = e.target.value;
    setUseCase(selectedCase);

    if (selectedCase === "not_listed") {
      if (files.length > 0) {
        applyUseCase("not_listed", files[0].name);
      } else {
        // No file yet, default all true
        resetAllOptions();
      }
    } else {
      // aadhar, address, facial
      let newOptions = {};
      allPiiKeys.forEach(k => { newOptions[k] = true; });

      if (selectedCase === "aadhar") {
        newOptions['aadhar'] = false;
        newOptions['person'] = false;
      } else if (selectedCase === "address") {
        newOptions['address'] = false;
        newOptions['person'] = false;
      } else if (selectedCase === "facial") {
        newOptions['person'] = false;
      }

      setPiiOptions(newOptions);
    }
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert("Please select at least one file or capture an image to upload.");
      return;
    }

    setProcessedFiles([]);
    setPublicUrl(null);
    setSendError(null);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    formData.append("piiOptions", JSON.stringify(piiOptions));

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data && response.data.processedFiles) {
        setProcessedFiles(response.data.processedFiles);
      } else if (response.data && response.data.error) {
        setError(response.data.error);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } catch (error) {
      console.error("Error uploading files:", error);
      setError("An error occurred while processing the files.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (fileObj) => {
    window.open(fileObj.download_url, "_blank");
    setProcessedFiles((prev) => prev.filter((f) => f.filename !== fileObj.filename));
  };

  const handleSendToS3 = async (filename) => {
    setSendLoading(true);
    setSendError(null);
    setPublicUrl(null);

    try {
      const response = await axios.post("http://127.0.0.1:5000/send_to_s3", { filename });

      if (response.data && response.data.public_url) {
        setPublicUrl(response.data.public_url);
        setProcessedFiles((prev) => prev.filter((f) => f.filename !== filename));
      } else if (response.data && response.data.error) {
        setSendError(response.data.error);
      } else {
        setSendError("An unexpected error occurred while sending to S3.");
      }
    } catch (error) {
      console.error("Error sending file to S3:", error);
      setSendError("An error occurred while uploading to S3.");
    } finally {
      setSendLoading(false);
    }
  };

  const dataURLtoFile = (dataurl, filename) => {
    let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      u8arr[i] = bstr.charCodeAt(i);
    }
    return new File([u8arr], filename, { type: mime });
  };

  const captureFromWebcam = () => {
    if (!webcamRef.current) return;
    const imageSrc = webcamRef.current.getScreenshot();
    if (imageSrc) {
      const randNum = Math.floor(Math.random() * 900) + 100; 
      const filename = `temp${randNum}.jpg`;

      const newFile = dataURLtoFile(imageSrc, filename);

      setFiles([newFile]);
      setPreviewSrc(imageSrc);

      resetAllOptions();
      if (useCase === "not_listed") {
        applyUseCase("not_listed", filename);
      } else if (useCase) {
        applyUseCase(useCase);
      }
    }
  };

  return (
    <div className="relative flex flex-col min-h-screen bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 p-6">
      <div className="text-center">
        <h1 className="mb-4 text-2xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl">
          REDACT <span className="underline underline-offset-3 decoration-8 decoration-blue-400">CREW</span>
        </h1>
        <p className="text-lg font-normal text-gray-500 lg:text-xl">
          Add your files or capture an image for easy redaction and secure sharing
        </p>
      </div>
      <br />
      <br />

      {/* Use-case selection */}
      <div className="mb-6 mx-auto w-full max-w-2xl bg-white p-4 rounded shadow">
        <h3 className="text-lg font-medium mb-2">Select your Use-Case:</h3>
        <div className="flex flex-col gap-2">
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="useCase"
              value="aadhar"
              checked={useCase === "aadhar"}
              onChange={handleUseCaseChange}
              className="mr-2"
            />
            Aadhar Verification
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="useCase"
              value="address"
              checked={useCase === "address"}
              onChange={handleUseCaseChange}
              className="mr-2"
            />
            Address Verification
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="useCase"
              value="facial"
              checked={useCase === "facial"}
              onChange={handleUseCaseChange}
              className="mr-2"
            />
            Facial Verification
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="useCase"
              value="not_listed"
              checked={useCase === "not_listed"}
              onChange={handleUseCaseChange}
              className="mr-2"
            />
            Not Listed / Unknown
          </label>
        </div>
      </div>

      {/* Sidebar for PII Options */}
      <div className="absolute right-0 top-0 h-full w-144 bg-white shadow-md p-6">
        <h3 className="mb-5 text-lg font-medium text-gray-900">Select PII Types to Redact:</h3>
        <ul className="grid w-full gap-6 md:grid-cols-1">
          {allPiiKeys.map((key) => (
            <li key={key}>
              <input
                type="checkbox"
                id={key}
                className="hidden peer"
                name={key}
                checked={piiOptions[key] === true}
                onChange={handleOptionChange}
              />
              <label
                htmlFor={key}
                className="inline-flex items-center justify-between w-full p-5 text-gray-500 bg-white border-2 border-gray-200 rounded-lg cursor-pointer 
                  peer-checked:border-blue-600 hover:text-gray-600 
                  peer-checked:text-gray-600 hover:bg-gray-50"
              >
                <div className="block">
                  <div className="w-full text-lg font-semibold capitalize">{key}</div>
                </div>
              </label>
            </li>
          ))}
        </ul>
      </div>

      {/* File Upload Section */}
      <div className="w-full max-w-2xl bg-white shadow-md rounded-lg p-6 mb-8 mx-auto">
        <h2 className="text-2xl font-semibold mb-4">Upload Your Files or Capture an Image</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors duration-300 ${
            isDragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-500 hover:bg-blue-50"
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center">
            <FaCloudUploadAlt className="text-6xl text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-blue-500">Drop the files here ...</p>
            ) : (
              <>
                <p className="text-gray-600">
                  Drag 'n' drop some files here, or click to select files
                </p>
                <em className="text-xs text-gray-500 mt-2">
                  (Images, PDFs, Word documents, and text files are supported)
                </em>
              </>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-col items-center">
          {!showWebcam && (
            <button
              onClick={() => setShowWebcam(true)}
              className="mt-4 px-6 py-3 rounded-lg font-bold shadow-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <FaCamera className="inline mr-2"/> Use Webcam
            </button>
          )}

          {showWebcam && (
            <div className="mt-4 flex flex-col items-center gap-4">
              <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                videoConstraints={{ facingMode: "user" }}
                className="rounded-lg border border-gray-300"
              />
              <button
                onClick={captureFromWebcam}
                className="px-6 py-3 rounded-lg font-bold shadow-md text-white bg-green-600 hover:bg-green-700"
              >
                Capture Photo
              </button>
              <button
                onClick={() => setShowWebcam(false)}
                className="px-6 py-3 rounded-lg font-bold shadow-md text-white bg-red-600 hover:bg-red-700"
              >
                Close Webcam
              </button>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div className="mt-4">
            <h3 className="text-lg font-medium mb-2">Selected Files:</h3>
            <ul className="space-y-2">
              {files.map((file, index) => (
                <li
                  key={index}
                  className="flex justify-between items-center bg-gray-50 p-2 rounded"
                >
                  <span>{file.name}</span>
                  <button
                    onClick={handleRemoveFile}
                    className="text-red-500 hover:text-red-700"
                  >
                    <FaTrash />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {previewSrc && (
          <div className="mt-6">
            <h3 className="text-xl font-medium mb-2">Preview:</h3>
            <div className="flex flex-col items-center gap-4">
              <img
                src={previewSrc}
                alt="Preview"
                className="max-w-full h-auto rounded-lg shadow-md"
              />
              <button
                onClick={handleRemoveFile}
                className="text-white bg-blue-600 hover:bg-blue-700 focus:ring focus:ring-blue-300 rounded-lg px-4 py-2 flex items-center"
              >
                <FaTrash className="mr-2" /> Remove
              </button>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || files.length === 0}
        className={`px-6 py-3 rounded-lg font-bold shadow-md mx-auto text-xl ${
          loading || files.length === 0
            ? "bg-gray-300 text-gray-600 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg focus:outline-none focus:ring focus:ring-blue-300"
        }`}
      >
        {loading ? (
          <>
            <FaSpinner className="animate-spin inline mr-2" /> Processing...
          </>
        ) : (
          "Submit"
        )}
      </button>

      {error && <div className="text-red-600 font-medium mt-4 text-center">{error}</div>}

      {processedFiles.length > 0 && (
        <div className="w-full max-w-2xl bg-white shadow-md rounded-lg p-6 mt-8 mx-auto">
          <h2 className="text-lg font-semibold mb-4">Processed Files</h2>
          <ul className="space-y-3">
            {processedFiles.map((fileObj, index) => (
              <li
                key={index}
                className="flex justify-between items-center bg-gray-50 p-3 rounded-lg shadow-sm hover:shadow-md"
              >
                <a
                  href={fileObj.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 underline"
                >
                  Download File {index + 1}
                </a>
                <div className="flex items-center gap-4">
                  <FaDownload
                    className="text-gray-700 hover:text-blue-600 cursor-pointer"
                    onClick={() => handleDownload(fileObj)}
                  />
                  <button
                    onClick={() => handleSendToS3(fileObj.filename)}
                    disabled={sendLoading}
                    className={`px-4 py-2 rounded-lg font-bold ${
                      sendLoading
                        ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                    }`}
                  >
                    {sendLoading ? "Sending..." : "Send"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sendError && (
        <div className="text-red-600 font-medium mt-4 text-center">{sendError}</div>
      )}

      {publicUrl && (
        <div className="text-green-600 font-semibold mt-4 text-center flex flex-col items-center gap-2">
          <div className="text-center">
            Public S3 URL:{" "}
            <a
              href={publicUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 underline break-all"
            >
              {publicUrl}
            </a>
          </div>
          <ShareButton publicUrl={publicUrl} />
        </div>
      )}
    </div>
  );
};

export default PiiRedaction;