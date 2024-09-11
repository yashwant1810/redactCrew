import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
    </div>
  );
};

export default Home;