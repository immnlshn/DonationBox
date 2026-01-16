export default function QRCodeInfo({ qrImageSrc, qrInfoText, alt }) {
  return (
    <section className="qr-code-info">
      <img src={qrImageSrc} alt={alt} className="qr-code-image" />
      <p className="qr-info-text">{qrInfoText}</p>
    </section>
  );
}
