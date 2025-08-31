        document.addEventListener('DOMContentLoaded', function() {
            // DOM Elements
            const notesInput = document.getElementById('notes-input');
            const generateBtn = document.getElementById('generate-btn');
            const exportBtn = document.getElementById('export-btn');
            const clearBtn = document.getElementById('clear-btn');
            const flashcardsContainer = document.getElementById('flashcards-container');
            const progressBar = document.getElementById('progress-bar');
            const loadingElement = document.getElementById('loading');
            const notification = document.getElementById('notification');
            
            // Sample flashcard data for demonstration
            const sampleFlashcards = [
                { question: "What is the capital of France?", answer: "Paris" },
                { question: "What is the largest planet in our solar system?", answer: "Jupiter" },
                { question: "Who wrote 'Romeo and Juliet'?", answer: "William Shakespeare" },
                { question: "What is the chemical symbol for gold?", answer: "Au" },
                { question: "What year did World War II end?", answer: "1945" }
            ];
            
            // Generate flashcards from notes
    generateBtn.addEventListener('click', async function() {
    const notes = notesInput.value.trim();
    const language = document.getElementById('language').value;
    
    if (notes === '') {
        showNotification('Please enter some notes first!', 'error');
        return;
    }
    
    // Show loading state
    loadingElement.style.display = 'block';
    generateBtn.disabled = true;
    
    try {
        const response = await fetch('http://localhost:5000/generate-flashcards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                notes: notes,
                language: language,
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Clear previous flashcards if any
        flashcardsContainer.innerHTML = '';
        
        // Display the generated flashcards
        data.flashcards.forEach(card => {
            createFlashcard(card.question, card.answer);
        });
        
        // Show success notification
        showNotification('Flashcards generated successfully!');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to generate flashcards. Using demo data instead.', 'error');
        
        // Fallback to demo data
        flashcardsContainer.innerHTML = '';
        sampleFlashcards.forEach(card => {
            createFlashcard(card.question, card.answer);
        });
    } finally {
        // Hide loading state
        loadingElement.style.display = 'none';
        generateBtn.disabled = false;
    }
});
            // Export functionality
            exportBtn.addEventListener('click', function() {
                if (flashcardsContainer.children.length === 0) {
                    showNotification('No flashcards to export!', 'error');
                    return;
                }
                
                showNotification('Export feature would save to database in a real application!');
            });
            
            // Clear all flashcards
            clearBtn.addEventListener('click', function() {
                flashcardsContainer.innerHTML = '';
                showNotification('All flashcards cleared');
            });
            
            // Create a flashcard element
            function createFlashcard(question, answer) {
                const flashcard = document.createElement('div');
                flashcard.className = 'flashcard';
                
                flashcard.innerHTML = `
                    <div class="flashcard-inner">
                        <div class="flashcard-front">
                            <div class="question">${question}</div>
                            <p><small>Click to flip</small></p>
                        </div>
                        <div class="flashcard-back">
                            <div class="answer">${answer}</div>
                            <p><small>Click to flip back</small></p>
                        </div>
                    </div>
                `;
                
                // Add flip interaction
                flashcard.addEventListener('click', function() {
                    this.classList.toggle('flipped');
                });
                
                flashcardsContainer.appendChild(flashcard);
            }
            
            // Simulate AI processing with progress bar
            function simulateProcessing() {
                return new Promise(resolve => {
                    let width = 0;
                    const interval = setInterval(() => {
                        if (width >= 100) {
                            clearInterval(interval);
                            resolve();
                        } else {
                            width += 5;
                            progressBar.style.width = width + '%';
                        }
                    }, 100);
                });
            }
            
            // Show notification
            function showNotification(message, type = 'success') {
                notification.textContent = message;
                notification.style.background = type === 'success' ? 'var(--success)' : 'var(--danger)';
                notification.classList.add('show');
                
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 3000);
            }
            
            // Add some sample text to the textarea for demonstration
            notesInput.value = "The French Revolution was a period of radical political and societal change in France that began with the Estates General of 1789 and ended with the formation of the French Consulate in November 1799. Many of its ideas are considered fundamental principles of liberal democracy, while its values and institutions remain central to modern French political discourse.";
        });

        