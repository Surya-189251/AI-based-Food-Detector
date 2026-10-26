import React from 'react'

const Section = ({ title, children }) => (
  <div className="card" style={{ marginBottom: '1.25rem' }}>
    <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--green-800)', marginBottom: '0.75rem' }}>
      {title}
    </h2>
    {children}
  </div>
)

export default function AboutPage() {
  return (
    <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '2rem' }}>
      <h1 className="page-title">About / How It Works</h1>
      <p className="page-subtitle">
        Architecture, image processing pipeline, model training, limitations, and future scope.
      </p>

      <Section title="Project Overview">
        <p>
          FreshCheck AI is an academic prototype demonstrating the use of deep learning for
          visible food freshness assessment. Users photograph a fruit and receive a freshness
          classification (Fresh / Moderately Fresh / Spoiled) along with an optional
          reference-based shelf-life estimate.
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          <strong>Important:</strong> FreshCheck AI assesses <em>visible</em> surface appearance
          only. It cannot detect internal spoilage, harmful bacteria, mycotoxins, or any
          contamination that is not externally visible.
        </p>
      </Section>

      <Section title="System Architecture">
        <ul style={{ paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li><strong>Frontend:</strong> React 18 + Vite — responsive single-page app.</li>
          <li><strong>Backend:</strong> Python 3.11 + FastAPI — REST API, async I/O.</li>
          <li><strong>Image preprocessing:</strong> Pillow (EXIF correction, resize) + OpenCV (blur/brightness checks).</li>
          <li><strong>Classification model:</strong> MobileNetV2 (transfer learning from ImageNet), fine-tuned on fruit freshness data.</li>
          <li><strong>Shelf-life logic:</strong> Rule-based reference table (USDA/FDA FoodKeeper).</li>
          <li><strong>Database:</strong> SQLite via aiosqlite — analysis history.</li>
          <li><strong>Uploads:</strong> UUID-named files in <code>backend/data/uploads/</code>.</li>
        </ul>
      </Section>

      <Section title="Image Processing Pipeline">
        <ol style={{ paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li><strong>Receive upload</strong> — validate MIME type, file size, and extension.</li>
          <li><strong>Decode &amp; verify</strong> — Pillow decodes and verifies the image; corrupted files are rejected.</li>
          <li><strong>EXIF correction</strong> — phone photos are auto-rotated to the correct orientation.</li>
          <li><strong>Quality checks</strong> — Laplacian variance (blur) and mean pixel brightness (over/under-exposure).</li>
          <li><strong>Resize</strong> — scale to 224×224 px (MobileNetV2 input size).</li>
          <li><strong>Normalise</strong> — pixel values scaled to [−1, 1] (MobileNetV2 convention).</li>
          <li><strong>Classify</strong> — softmax probabilities across all classes.</li>
          <li><strong>Threshold</strong> — if the top probability &lt; 0.60 or the food type is unsupported, return "Unable to assess".</li>
        </ol>
      </Section>

      <Section title="Model Training">
        <p>
          The classifier uses MobileNetV2 pre-trained on ImageNet. Training proceeds in two phases:
        </p>
        <ol style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', lineHeight: 2 }}>
          <li><strong>Phase 1</strong> — freeze all MobileNetV2 layers; train a new classification head (Dense 256 → Dropout → Softmax).</li>
          <li><strong>Phase 2</strong> — unfreeze the last 50 MobileNetV2 layers; fine-tune with a lower learning rate (1 × 10⁻⁵).</li>
        </ol>
        <p style={{ marginTop: '0.5rem' }}>
          <strong>Dataset:</strong> "Fruits fresh and rotten for classification" (Kaggle, Sriram Reddy).
          This dataset contains Fresh and Spoiled classes only.
          A real three-class model (Fresh / Moderately Fresh / Spoiled) would require additional
          labeled images of fruit in intermediate stages of ripening.
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          <strong>Evaluation metrics:</strong> Per-class precision, recall, F1 score, macro F1,
          and a confusion matrix are produced by <code>ml/evaluation/evaluate.py</code>.
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          No pre-trained weights are bundled with this repository. Reported accuracy and confidence
          scores reflect the model you train locally. Do not quote placeholder numbers as real results.
        </p>
      </Section>

      <Section title="Shelf-Life Estimation">
        <p>
          Shelf-life estimates are <strong>reference-based</strong>, not model-predicted.
          They use verified ranges from the USDA FoodKeeper App and FDA Food Safety guidelines,
          adjusted for storage condition (room temperature vs. refrigerated), whole vs. cut,
          and elapsed days since purchase (if provided).
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          No longitudinal training dataset (images captured over multiple days of the same piece
          of fruit) is available in this version. A true learned shelf-life regression model would
          require such data, with documented storage conditions and measured ground-truth shelf life.
        </p>
      </Section>

      <Section title="Camera Access — Technical Notes">
        <ul style={{ paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>Browser camera access (getUserMedia) requires <strong>HTTPS or localhost</strong>.</li>
          <li>On localhost (development): no extra steps needed.</li>
          <li>
            On a real phone over your local network: run the backend with{' '}
            <code>uvicorn … --host 0.0.0.0</code> and the frontend with{' '}
            <code>vite --host</code>, then set up a self-signed certificate or use{' '}
            <a href="https://ngrok.com" target="_blank" rel="noopener noreferrer">ngrok</a>{' '}
            to expose HTTPS. See <code>docs/DEPLOYMENT.md</code> for details.
          </li>
          <li>The rear camera is preferred via <code>facingMode: "environment"</code>.</li>
          <li>Front/rear switching is offered when multiple cameras are available.</li>
          <li>All MediaStream tracks are stopped when the camera view is closed.</li>
        </ul>
      </Section>

      <Section title="Limitations">
        <ul style={{ paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>Only surface appearance is analysed — internal spoilage is invisible to the camera.</li>
          <li>Accuracy depends heavily on image quality, lighting, and background clutter.</li>
          <li>Model trained on only 6 classes (fresh/spoiled for apple, banana, orange).</li>
          <li>No "Moderately Fresh" class in the current training data.</li>
          <li>Shelf-life ranges are approximate averages; actual life varies widely.</li>
          <li>The system has not been validated in a clinical or regulatory food-safety context.</li>
          <li>Do not use this tool as a substitute for professional food-safety assessment.</li>
        </ul>
      </Section>

      <Section title="Future Scope">
        <ul style={{ paddingLeft: '1.25rem', lineHeight: 2 }}>
          <li>Expand supported foods (tomatoes, strawberries, leafy vegetables, etc.).</li>
          <li>Add a "Moderately Fresh" class with appropriate training data.</li>
          <li>Implement a learned shelf-life regression model from longitudinal image data.</li>
          <li>Object detection to isolate the fruit from the background.</li>
          <li>Mold / defect localisation using segmentation models.</li>
          <li>Multi-user support with authentication.</li>
          <li>Export history to CSV for academic reporting.</li>
        </ul>
      </Section>

      <div className="safety-notice">
        ⚠️ This tool assesses visible freshness only. It cannot detect all harmful bacteria,
        toxins, or internal spoilage and cannot confirm food safety.
      </div>
    </div>
  )
}
