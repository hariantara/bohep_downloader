// Mock browser environment
var window = {
    location: { href: '' }
};
var document = {
    write: console.log,
    createElement: function() { return {}; },
    getElementsByTagName: function() { return []; }
};
var navigator = {
    userAgent: 'Mozilla/5.0'
};

// Get the packed JavaScript from command line argument
const packedJs = process.argv[2];

if (!packedJs) {
    console.error('Please provide packed JavaScript as an argument');
    process.exit(1);
}

try {
    // Evaluate the packed JavaScript
    eval('console.log(' + packedJs + ')');
} catch (error) {
    console.error('Error decoding:', error.message);
    process.exit(1);
} 