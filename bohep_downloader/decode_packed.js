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
    console.log('Starting JavaScript decoding process...');
    
    // First try to evaluate the packed JavaScript directly
    try {
        console.log('Attempting direct evaluation...');
        eval('console.log(' + packedJs + ')');
    } catch (evalError) {
        console.error('Direct eval failed:', evalError.message);
        
        // Try to extract URLs directly from the packed JavaScript
        console.log('Attempting to extract URLs directly...');
        const urlMatches = packedJs.match(/https:\/\/[^\'"\s]+\.m3u8/g);
        if (urlMatches && urlMatches.length > 0) {
            console.log('Found URLs directly in the packed JavaScript:');
            urlMatches.forEach(url => console.log(url));
        } else {
            // If no URLs found, try to extract the function body
            console.log('Attempting to extract function body...');
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
                } else {
                    // Try to find URLs with a more lenient pattern
                    console.log('Attempting to find URLs with a more lenient pattern...');
                    const lenientMatches = functionBody.match(/https:\/\/[^\'"\s]+/g);
                    if (lenientMatches && lenientMatches.length > 0) {
                        console.log('Found potential URLs:');
                        lenientMatches.forEach(url => console.log(url));
                    } else {
                        // Try to extract URLs from string literals
                        console.log('Attempting to extract URLs from string literals...');
                        const stringMatches = functionBody.match(/"([^"]+)"/g) || functionBody.match(/'([^']+)'/g);
                        if (stringMatches && stringMatches.length > 0) {
                            console.log('Found string literals:');
                            stringMatches.forEach(str => {
                                const cleanStr = str.replace(/['"]/g, '');
                                if (cleanStr.includes('http') && cleanStr.includes('.m3u8')) {
                                    console.log(cleanStr);
                                }
                            });
                        } else {
                            // If all else fails, just output the raw packed JavaScript
                            console.log('Raw packed JavaScript:');
                            console.log(packedJs);
                        }
                    }
                }
            } else {
                // Try to find URLs with a more lenient pattern in the entire packed JS
                console.log('Attempting to find URLs with a more lenient pattern in the entire packed JS...');
                const lenientMatches = packedJs.match(/https:\/\/[^\'"\s]+/g);
                if (lenientMatches && lenientMatches.length > 0) {
                    console.log('Found potential URLs:');
                    lenientMatches.forEach(url => console.log(url));
                } else {
                    // Try to extract URLs from string literals
                    console.log('Attempting to extract URLs from string literals...');
                    const stringMatches = packedJs.match(/"([^"]+)"/g) || packedJs.match(/'([^']+)'/g);
                    if (stringMatches && stringMatches.length > 0) {
                        console.log('Found string literals:');
                        stringMatches.forEach(str => {
                            const cleanStr = str.replace(/['"]/g, '');
                            if (cleanStr.includes('http') && cleanStr.includes('.m3u8')) {
                                console.log(cleanStr);
                            }
                        });
                    } else {
                        // Try to extract URLs from base64 encoded content
                        console.log('Attempting to extract URLs from base64 encoded content...');
                        const base64Matches = packedJs.match(/atob\(['"]([^'"]+)['"]\)/g);
                        if (base64Matches && base64Matches.length > 0) {
                            console.log('Found base64 encoded content:');
                            base64Matches.forEach(base64 => {
                                try {
                                    const decoded = Buffer.from(base64.match(/atob\(['"]([^'"]+)['"]\)/)[1], 'base64').toString('utf-8');
                                    console.log('Decoded base64 content:');
                                    console.log(decoded);
                                    
                                    // Try to find URLs in the decoded content
                                    const decodedUrlMatches = decoded.match(/https:\/\/[^\'"\s]+\.m3u8/g);
                                    if (decodedUrlMatches && decodedUrlMatches.length > 0) {
                                        console.log('Found URLs in decoded base64 content:');
                                        decodedUrlMatches.forEach(url => console.log(url));
                                    }
                                } catch (e) {
                                    console.error('Error decoding base64 content:', e.message);
                                }
                            });
                        } else {
                            // If all else fails, just output the raw packed JavaScript
                            console.log('Raw packed JavaScript:');
                            console.log(packedJs);
                        }
                    }
                }
            }
        }
    }
} catch (error) {
    console.error('Error decoding:', error.message);
    process.exit(1);
} 