import "../App.css";

export default function About() {
  return (
    <div className="chat-panel">
      <h2 style={{ color: "#ff8c42" }}>About This Project</h2>

      <p>
        <strong>GENAI Training Intern</strong> is a demo and training project
        focused on learning and experimenting with generative AI applications.
      </p>

      <h3 style={{ color: "#ff8c42" }}>Prerequisites</h3>
      <ul>
        <li>Git installed</li>
        <li>Python 3.8+ or Node.js 14+/16+</li>
        <li>(Optional) Docker</li>
      </ul>

      <h3 style={{ color: "#ff8c42" }}>Running Locally</h3>

      <p><strong>Python:</strong></p>
      <ul>
        <li>Create virtual environment</li>
        <li>Install: <code>pip install -r requirements.txt</code></li>
        <li>Run: <code>python app.py</code></li>
      </ul>

      <p><strong>Node:</strong></p>
      <ul>
        <li><code>npm install</code></li>
        <li><code>npm run dev</code></li>
      </ul>

      <h3 style={{ color: "#ff8c42" }}>Contributing</h3>
      <p>
        Fork the repository, create a feature branch, add your changes,
        and submit a pull request.
      </p>

      <h3 style={{ color: "#ff8c42" }}>Contact</h3>
      <p>
        Maintainer: <strong>Gurdeepsingh-10</strong> <br />
        Use GitHub issues for questions or help.
      </p>
    </div>
  );
}
