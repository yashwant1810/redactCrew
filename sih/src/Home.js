import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FaLinkedin, FaGithub, FaInstagram, FaNpm } from 'react-icons/fa'; // Added NPM icon
import "./Home.css";

const Home = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let interval = null;

    const h1 = document.querySelector("h1");
    h1.onmouseover = (event) => {
      let iteration = 0;
      clearInterval(interval);

      interval = setInterval(() => {
        event.target.innerText = event.target.innerText
          .split("")
          .map((letter, index) => {
            if (index < iteration) {
              return event.target.dataset.value[index];
            }
            return letters[Math.floor(Math.random() * 26)];
          })
          .join("");

        if (iteration >= event.target.dataset.value.length) {
          clearInterval(interval);
        }

        iteration += 1 / 3;
      }, 30);
    };

    h1.onclick = () => {
      navigate("/pii-redaction"); // Navigate to the PII Redaction page
    };

    return () => clearInterval(interval);
  }, [navigate]);

  return (
    <div className="App">
      <h1 data-value="AI PII REDACTION">AI PII REDACTION</h1>

      <div className="project-description">
        <div className="description-section">
          <h2>What We Offer</h2>
          <p>
            We provide state-of-the-art PII redaction services for documents and images, ensuring privacy and compliance with security standards.
          </p>
        </div>

        <div className="description-section">
          <h2>How We Work</h2>
          <p>
            Upload your documents, select the types of PII you want to redact, and we’ll process everything in seconds, providing you with safe, ready-to-download files.
          </p>
        </div>

        <div className="description-section">
          <h2>Integrate Our Solution</h2>
          <p>
            You can easily integrate our service into your existing website or app by either calling our web-based API for automation or downloading our npm package to embed directly in your project.
          </p>
          <div className="social-icons">
            <a href="https://www.npmjs.com/package/sih_package" target="_blank" rel="noopener noreferrer">
              <FaNpm className="social-icon npm-icon" /> {/* NPM Icon */}
            </a>
          </div>
        </div>

        <div className="description-section">
          <h2>Connect with Us</h2>
          <div className="social-icons">
            <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer">
              <FaLinkedin className="social-icon" />
            </a>
            <a href="https://github.com/yashwant1810" target="_blank" rel="noopener noreferrer">
              <FaGithub className="social-icon" />
            </a>
            <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer">
              <FaInstagram className="social-icon" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;