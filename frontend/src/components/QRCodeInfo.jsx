export default function QRCodeInfo({ qrImageSrc, clubLogoSrc, qrInfoText, alt, children }) {
  return (
    <section className="qr-code-info">
      <div className="qr-logo-row">
        <img className="qr-code-image" src={qrImageSrc} alt={alt} />
        <img className="club-logo" src={clubLogoSrc} alt="Vereinslogo" />
      </div>

      <div className="qr-right">
        {children}
        <p className="qr-info-text">{qrInfoText}</p>
      </div>
    </section>
  );
}
