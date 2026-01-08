export default function QRCodeInfo({ qrImageSrc, clubLogoSrc, qrInfoText, alt }) {
  return (
    <section className="qr-code-info">
      <div className="qr-logo-row">
        <img className="qr-code-image" src={qrImageSrc} alt={alt} />
        <img className="club-logo" src={clubLogoSrc} alt="Vereinslogo" />
      </div>

      <p className="qr-info-text">{qrInfoText}</p>
    </section>
  );
}
