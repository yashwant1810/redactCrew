import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FaLinkedin, FaGithub, FaInstagram, FaNpm } from "react-icons/fa";

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
      navigate("/pii-redaction");
    };

    return () => clearInterval(interval);
  }, [navigate]);

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen text-black"
      style={{
        backgroundColor: "#F3F4F6",
        fontSize: "14px",
        fontWeight: "400",
        fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      }}
    >
      <h1
        data-value="REDACT"
        className="text-4xl sm:text-5xl lg:text-7xl font-extrabold p-6 bg-blue-700 text-transparent bg-clip-text hover:text-blue-700 transition-transform duration-300 hover:scale-110 cursor-pointer"
      >
        REDACT
      </h1>

      <div className="mt-12 text-center grid gap-8 max-w-6xl bg-white rounded-lg shadow-lg p-12 border border-gray-200">
        {/* Section 1 */}
        <div className="bg-gray-50 rounded-lg p-6 hover:bg-gray-100 transition-all duration-300">
          <h2 className="text-2xl font-bold text-blue-600 mb-4">What We Offer</h2>
          <p className="text-gray-700">
            We provide state-of-the-art redaction services for documents and
            images, ensuring privacy and compliance with security standards.
          </p>
        </div>

        {/* Section 2 */}
        <div className="bg-gray-50 rounded-lg p-6 hover:bg-gray-100 transition-all duration-300">
          <h2 className="text-2xl font-bold text-blue-600 mb-4">How We Work</h2>
          <p className="text-gray-700">
            Upload your documents, select the types of information you want to
            redact, and we'll process everything in seconds, providing you with
            safe, ready-to-download files. We also provide npm package and API
            to seamlessly integrate it into your workflow.
          </p>
        </div>

        {/* Section 3 */}
        <div className="bg-gray-50 rounded-lg p-6 hover:bg-gray-100 transition-all duration-300">
          <h2 className="text-2xl font-bold text-blue-600 mb-4">
            Integrate Our Solution
          </h2>
          <p className="text-gray-700">
            You can easily integrate our service into your existing website or
            app by either calling our web-based API for automation or
            downloading our npm package to embed directly in your project.
          </p>
          <div className="flex justify-center gap-6 mt-4">
            <a
              href="https://www.npmjs.com/package/pii-redactor"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 transition-transform transform hover:scale-110"
            >
              <FaNpm size={30} />
            </a>
          </div>
        </div>

        {/* Section 4 */}
        <div className="bg-gray-50 rounded-lg p-6 hover:bg-gray-100 transition-all duration-300">
          <h2 className="text-2xl font-bold text-blue-600 mb-4">Connect with Us</h2>
          <div className="flex justify-center gap-6">
            <a
              href="https://www.linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 transition-transform transform hover:scale-110"
            >
              <FaLinkedin size={30} />
            </a>
            <a
              href="https://github.com/yashwant1810"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 transition-transform transform hover:scale-110"
            >
              <FaGithub size={30} />
            </a>
            <a
              href="https://www.instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-pink-500 hover:text-pink-700 transition-transform transform hover:scale-110"
            >
              <FaInstagram size={30} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;