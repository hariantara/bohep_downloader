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
    // First try to evaluate the packed JavaScript directly
    try {
        eval('console.log(' + packedJs + ')');
    } catch (evalError) {
        console.error('Direct eval failed:', evalError.message);
        
        // Try to extract URLs directly from the packed JavaScript
        const urlMatches = packedJs.match(/https:\/\/[^\'"\s]+\.m3u8/g);
        if (urlMatches && urlMatches.length > 0) {
            console.log('Found URLs directly in the packed JavaScript:');
            urlMatches.forEach(url => console.log(url));
        } else {
            // If no URLs found, try to extract the function body
            const functionMatch = packedJs.match(/function\s*\([^)]*\)\s*\{([\s\S]*)\}/);
            if (functionMatch) {
                const functionBody = functionMatch[1];
                console.log('Function body extracted:');
                console.log(functionBody);
                
                // Try to find URLs in the function body
                const bodyUrlMatches = functionBody.match(/https:\/\/[^\'"\s]+\.m3u8/g);
                if (bodyUrlMatches && bodyUrlMatches.length > 0) {
                    console.log('Found URLs in function body:');
                    bodyUrlMatches.forEach(url => console.log(url));
                }
            } else {
                // If all else fails, just output the raw packed JavaScript
                console.log('Raw packed JavaScript:');
                console.log(packedJs);
            }
        }
    }
} catch (error) {
    console.error('Error decoding:', error.message);
    process.exit(1);
} 