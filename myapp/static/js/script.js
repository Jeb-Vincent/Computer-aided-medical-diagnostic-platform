document.getElementById('imageForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // 显示加载指示器
    var loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'flex';  // 使用Flex布局来居中加载指示器
    document.querySelector('#imageForm button').disabled = true; // 禁用按钮防止重复提交

    const formData = new FormData(this);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/process_image/', true);

    // 如果使用的是Django框架，确保csrftoken cookie存在
    if (getCookie('csrftoken')) {
        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    }

    xhr.responseType = 'blob';

    xhr.onload = function() {
        if (xhr.status === 200) {
            // 模拟五秒延迟后隐藏加载指示器并显示结果图片
            setTimeout(function() {
                // 隐藏加载指示器
                loadingIndicator.style.display = 'none';
                document.querySelector('#imageForm button').disabled = false; // 启用按钮

                // 显示结果部分
                document.getElementById('resultSection').classList.remove('hidden');
                const url = URL.createObjectURL(xhr.response);
                document.getElementById('processedImage').src = url;
                document.getElementById('downloadLink').href = url;
            }, 2000); // 2秒延迟
        } else {
            alert('Error processing image.');

            // 隐藏加载指示器并启用按钮
            loadingIndicator.style.display = 'none';
            document.querySelector('#imageForm button').disabled = false;
        }
    };

    xhr.onerror = function() {
        alert('Network error occurred.');

        // 隐藏加载指示器并启用按钮
        loadingIndicator.style.display = 'none';
        document.querySelector('#imageForm button').disabled = false;
    };

    xhr.send(formData);
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}