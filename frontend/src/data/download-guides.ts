export interface DownloadGuide {
  id: string;
  institution: string;
  accountType: string;
  steps: string[];
  headerFormat: string;
  tips: string[];
}

export const downloadGuides: DownloadGuide[] = [
  {
    id: "chase_credit",
    institution: "Chase",
    accountType: "Credit Card",
    steps: [
      "Log in to chase.com and select your credit card account",
      "Click the download icon (arrow) in the transaction activity section",
      'Select "CSV" as the file format',
      "Choose your date range (Chase limits downloads to 90 days at a time)",
      'Click "Download" — the file will be named like Chase1234_Activity.CSV',
    ],
    headerFormat: "Transaction Date, Post Date, Description, Category, Type, Amount, Memo",
    tips: [
      "Chase limits CSV downloads to 90-day windows. For a full year, you'll need 4-5 separate downloads.",
      "Chase includes a built-in Category column (Food & Drink, Shopping, etc.) which nullbook preserves.",
      "The filename includes the last 4 digits of your card number.",
    ],
  },
  {
    id: "chase_checking",
    institution: "Chase",
    accountType: "Checking",
    steps: [
      "Log in to chase.com and select your checking account",
      "Click the download icon in the transaction activity section",
      'Select "CSV" as the file format',
      "Choose your date range",
      "Download the file",
    ],
    headerFormat: "Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #",
    tips: [
      "Checking CSVs have a different format than credit card CSVs — nullbook detects both automatically.",
      "Checking transactions don't include the Category column that credit cards have.",
    ],
  },
  {
    id: "capital_one",
    institution: "Capital One",
    accountType: "Credit Card",
    steps: [
      "Log in to capitalone.com and select your credit card",
      "Go to Statements & Activity",
      'Click "Download Transactions"',
      "Select CSV format and your desired date range",
      "Download the file",
    ],
    headerFormat: "Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit",
    tips: [
      "Capital One uses separate Debit and Credit columns instead of a single Amount column.",
      "The Category column is similar to Chase's built-in categories.",
    ],
  },
  {
    id: "bass_pro",
    institution: "Bass Pro / Cabela's",
    accountType: "Credit Card (Capital One)",
    steps: [
      "Log in to capitalone.com (Bass Pro / Cabela's cards are issued by Capital One)",
      "Select your Bass Pro or Cabela's credit card",
      'Click "Download Transactions" in the activity section',
      "Select CSV format and your date range",
      "Download the file",
    ],
    headerFormat: "Date, Description, Amount, Balance",
    tips: [
      "Bass Pro / Cabela's cards are managed through Capital One's website.",
      "The CSV format is simpler than Capital One's standard card format.",
    ],
  },
  {
    id: "amex",
    institution: "American Express",
    accountType: "Credit Card",
    steps: [
      "Log in to americanexpress.com",
      "Go to Statements & Activity",
      'Click "Download Your Statement Data"',
      "Select CSV format",
      "Choose the statement period(s) you want",
      "Download the file",
    ],
    headerFormat: "Date, Description, Amount, Extended Details, ..., Category",
    tips: [
      "Amex treats charges as positive numbers (opposite of Chase). nullbook handles this automatically.",
      "You can download multiple statement periods at once.",
      "Amex includes an Extended Details field with additional merchant info.",
    ],
  },
  {
    id: "bank_of_america",
    institution: "Bank of America",
    accountType: "Checking / Savings",
    steps: [
      "Log in to bankofamerica.com",
      "Select your checking or savings account",
      'Click "Download Account Activity"',
      "Choose Microsoft Excel or CSV format",
      "Select your date range and download",
    ],
    headerFormat: "Date, Description, Amount, Running Bal.",
    tips: [
      "Bank of America's CSV format is straightforward with 4 columns.",
      "Date ranges up to 18 months are available for download.",
    ],
  },
  {
    id: "wells_fargo",
    institution: "Wells Fargo",
    accountType: "Checking / Savings",
    steps: [
      "Log in to wellsfargo.com",
      "Select your account",
      'Click "Download Account Activity" at the bottom of the activity page',
      'Choose "Comma Separated" format',
      "Select your date range and download",
    ],
    headerFormat: "Date, Amount, *, *, Description",
    tips: [
      "Wells Fargo CSVs sometimes lack a header row — nullbook handles both cases.",
      "Downloads are limited to 18 months of history.",
    ],
  },
  {
    id: "amazon",
    institution: "Amazon",
    accountType: "Order History",
    steps: [
      "Go to amazon.com/hz/privacy-central/data-requests/preview.html",
      'Or navigate: Account → Your Account → "Request Your Data"',
      'Select "Your Orders" and submit the request',
      "Wait for Amazon to process (usually 1-3 days)",
      "Download the ZIP file from the email Amazon sends you",
      'Extract and find "Retail.OrderHistory.1.csv" inside',
    ],
    headerFormat: "Order Date, Order ID, Title, Category, ASIN, Quantity, Total Owed, ...",
    tips: [
      "Amazon's data export includes ALL orders, not just the current year.",
      "nullbook can cross-reference Amazon orders with bank charges to identify what each 'AMAZON MKTPL*' charge was for.",
      "The export takes 1-3 days to process — request it early.",
    ],
  },
  {
    id: "coinbase",
    institution: "Coinbase",
    accountType: "Crypto Exchange",
    steps: [
      "Log in to coinbase.com",
      "Go to Taxes → Documents (or Settings → Taxes)",
      "Download your 1099-DA form (if available for the tax year)",
      'For transaction history: go to Reports → "Generate report"',
      "Select Transaction History and your date range",
      "Download the CSV file",
    ],
    headerFormat:
      "Timestamp, Transaction Type, Asset, Quantity Transacted, Spot Price, Subtotal, Total, Fees, Notes",
    tips: [
      "Coinbase issues a 1099-DA for digital asset transactions starting from 2025.",
      "The transaction history CSV includes buys, sells, converts, sends, and receives.",
      "For cost basis tracking, download the full transaction history from account creation.",
    ],
  },
];

export function getGuideByInstitution(institution: string): DownloadGuide[] {
  return downloadGuides.filter((g) => g.institution.toLowerCase() === institution.toLowerCase());
}

export function searchGuides(query: string): DownloadGuide[] {
  const q = query.toLowerCase();
  return downloadGuides.filter(
    (g) =>
      g.institution.toLowerCase().includes(q) ||
      g.accountType.toLowerCase().includes(q) ||
      g.id.includes(q)
  );
}
