import { createRoot } from "react-dom/client";
import UploadForm from "./form.jsx";
import Title from "./title.jsx";

function App() {
  return (
    <main>
      <Title />
      <UploadForm />
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);