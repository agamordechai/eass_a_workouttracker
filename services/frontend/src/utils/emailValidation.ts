/**
 * Email validation utilities with typo detection for common domains.
 */

// Common typos mapped to their correct domain
const DOMAIN_TYPOS: Record<string, string> = {
  // Gmail typos
  'gmial.com': 'gmail.com',
  'gmaik.com': 'gmail.com',
  'gmal.com': 'gmail.com',
  'gmali.com': 'gmail.com',
  'gmail.co': 'gmail.com',
  'gmail.cm': 'gmail.com',
  'gmail.om': 'gmail.com',
  'gmail.con': 'gmail.com',
  'gmail.cpm': 'gmail.com',
  'gmai.com': 'gmail.com',
  'gmailcom': 'gmail.com',
  'gmail.vom': 'gmail.com',
  'gamil.com': 'gmail.com',
  'gnail.com': 'gmail.com',
  'g]mail.com': 'gmail.com',
  // Yahoo typos
  'yaho.com': 'yahoo.com',
  'yahooo.com': 'yahoo.com',
  'yahoo.co': 'yahoo.com',
  'yahoo.cm': 'yahoo.com',
  'yahoo.con': 'yahoo.com',
  'yaoo.com': 'yahoo.com',
  'yhaoo.com': 'yahoo.com',
  // Hotmail typos
  'hotmal.com': 'hotmail.com',
  'hotmai.com': 'hotmail.com',
  'hotmail.co': 'hotmail.com',
  'hotmail.cm': 'hotmail.com',
  'hotmail.con': 'hotmail.com',
  'hotmial.com': 'hotmail.com',
  'hotamil.com': 'hotmail.com',
  // Outlook typos
  'outlok.com': 'outlook.com',
  'outloo.com': 'outlook.com',
  'outlook.co': 'outlook.com',
  'outlook.cm': 'outlook.com',
  'outlook.con': 'outlook.com',
  'outllok.com': 'outlook.com',
  // iCloud typos
  'icloud.co': 'icloud.com',
  'icloud.cm': 'icloud.com',
  'icloud.con': 'icloud.com',
  'icoud.com': 'icloud.com',
  'iclod.com': 'icloud.com',
};

export interface EmailValidationResult {
  isValid: boolean;
  error?: string;
  suggestion?: string;
}

/**
 * Validates an email address for proper format and common typos.
 */
export function validateEmail(email: string): EmailValidationResult {
  const trimmedEmail = email.trim().toLowerCase();

  // Check if empty
  if (!trimmedEmail) {
    return { isValid: false, error: 'Email is required' };
  }

  // Basic email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(trimmedEmail)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  // More strict validation
  const strictEmailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  if (!strictEmailRegex.test(trimmedEmail)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  // Extract domain
  const atIndex = trimmedEmail.lastIndexOf('@');
  const domain = trimmedEmail.substring(atIndex + 1);

  // Check for common domain typos
  if (DOMAIN_TYPOS[domain]) {
    const correctedEmail = trimmedEmail.replace(domain, DOMAIN_TYPOS[domain]);
    return {
      isValid: false,
      error: `Did you mean ${correctedEmail}?`,
      suggestion: correctedEmail,
    };
  }

  // Check for suspicious TLDs that are often typos
  const tld = domain.substring(domain.lastIndexOf('.'));
  if (['.con', '.cm', '.vom', '.cpm', '.om'].includes(tld)) {
    const correctedDomain = domain.slice(0, -tld.length) + '.com';
    const correctedEmail = trimmedEmail.replace(domain, correctedDomain);
    return {
      isValid: false,
      error: `Did you mean ${correctedEmail}?`,
      suggestion: correctedEmail,
    };
  }

  // Check minimum domain length (at least x.xx)
  if (domain.length < 4) {
    return { isValid: false, error: 'Please enter a valid email domain' };
  }

  // Check TLD length (at least 2 characters)
  if (tld.length < 3) { // Including the dot
    return { isValid: false, error: 'Please enter a valid email domain' };
  }

  return { isValid: true };
}


