const box1 = document.getElementById('one');
box1.addEventListener('mouseover', function handleMouseOver() {
    box1.style.color = 'blue';
});

box1.addEventListener('mouseout', function handleMouseOut() {
    box1.style.color = 'whitesmoke';
});

const box2 = document.getElementById('two');
box2.addEventListener('mouseover', function handleMouseOver() {
    box2.style.color = 'blue';
});
box2.addEventListener('mouseout', function handleMouseOut() {
    box2.style.color = 'whitesmoke';
});
