function search() {
    const query = document.getElementById('searchInput').value;
    console.log('搜索关键词:', query);

    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">搜索中...</div>';

    fetch(`/search?q=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('搜索请求失败');
            }
            return response.json();
        })
        .then(data => {
            console.log('搜索结果:', data);
            let html = '';
            
            if (data.companies && data.companies.length > 0) {
                data.companies.forEach(company => {
                    html += `
                        <div class="company-card">
                            <h3>${company.name}</h3>
                            <p class="company-location"><strong>国家/地区：</strong>${company.country}</p>
                            <p class="company-desc">${company.description}</p>
                            <p class="certification-status"><strong>认证状态：</strong>${company.certification_status}</p>
                        </div>
                    `;
                });
            } else {
                html = '<div class="no-results">未找到相关结果</div>';
            }
            
            resultsDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('搜索错误:', error);
            resultsDiv.innerHTML = '<div class="error">搜索出错，请稍后重试</div>';
        });
}

// 添加回车键搜索功能
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        search();
    }
});

// 为搜索按钮添加点击事件
document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.querySelector('button');
    if (searchButton) {
        searchButton.addEventListener('click', search);
    }
}); 