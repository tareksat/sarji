import { useState } from 'react';
import { CheckIcon, CopyIcon } from './icons';

export default function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access denied or unavailable; no-op.
    }
  };

  return (
    <button
      className="meta-btn copy-btn"
      onClick={handleCopy}
      title={copied ? 'Copied' : 'Copy message'}
      aria-label={copied ? 'Copied' : 'Copy message'}
    >
      {copied ? <CheckIcon width={13} height={13} /> : <CopyIcon width={13} height={13} />}
    </button>
  );
}
