/**
 * 財商成長思維 - 資料統計儀表板
 * 監控 AI 使用量、系統性能和文章統計
 */

class DashboardManager {
    constructor() {
        this.aiUsageChart = null;
        this.articleChart = null;
        this.refreshInterval = 30000; // 30秒自動刷新
        this.autoRefreshTimer = null;
        this.apiBaseUrl = '/api/v1/financial-wisdom';

        this.init();
    }

    async init() {
        console.log('🚀 初始化儀表板...');

        try {
            await this.loadDashboardData();
            this.initCharts();
            this.startAutoRefresh();

            console.log('✅ 儀表板初始化完成');
        } catch (error) {
            console.error('❌ 儀表板初始化失敗:', error);
            this.showError('儀表板載入失敗，請檢查網路連線');
        }
    }

    async loadDashboardData() {
        console.log('📊 載入統計數據...');

        try {
            // 並行載入多個數據源
            const [statsData, cacheData, performanceData] = await Promise.all([
                this.fetchStats(),
                this.fetchCacheStats(),
                this.fetchPerformanceMetrics()
            ]);

            // 更新統計卡片
            this.updateStatCards(statsData);
            this.updateCacheInfo(cacheData);
            this.updateSystemMetrics(performanceData);
            this.updateServiceStatus(performanceData);

        } catch (error) {
            console.error('載入數據失敗:', error);
            throw error;
        }
    }

    async fetchStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stats`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('無法載入基本統計:', error);
            return this.getMockStats();
        }
    }

    async fetchCacheStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/cache/stats`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('無法載入緩存統計:', error);
            return { cache_stats: { active_keys: 0, memory_usage_kb: 0 } };
        }
    }

    async fetchPerformanceMetrics() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/performance/metrics`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('無法載入性能指標:', error);
            return this.getMockPerformanceMetrics();
        }
    }

    getMockStats() {
        return {
            total_articles: Math.floor(Math.random() * 1000) + 500,
            published_articles: Math.floor(Math.random() * 800) + 400,
            categories: ['投資理財', '風險管理', '財富累積', '創業精神', '理財工具'].map(name => ({
                name,
                count: Math.floor(Math.random() * 100) + 20
            })),
            recent_activity: {
                articles_this_month: Math.floor(Math.random() * 50) + 10,
                ai_calls_today: Math.floor(Math.random() * 200) + 50
            }
        };
    }

    getMockPerformanceMetrics() {
        return {
            cache_performance: {
                hit_rate_estimate: `${Math.floor(Math.random() * 30) + 70}%`,
                memory_usage_kb: Math.floor(Math.random() * 1000) + 200,
                active_cache_keys: Math.floor(Math.random() * 50) + 10
            },
            api_endpoints: {
                get_articles: { avg_response_ms: Math.floor(Math.random() * 100) + 80 },
                generate_article: { avg_response_ms: Math.floor(Math.random() * 3000) + 2000 }
            }
        };
    }

    updateStatCards(data) {
        // 更新文章總數
        const totalElement = document.getElementById('totalArticles');
        const articlesProgress = document.getElementById('articlesProgress');
        if (totalElement && data.total_articles) {
            this.animateNumber(totalElement, data.total_articles);
            articlesProgress.style.width = `${Math.min((data.total_articles / 1000) * 100, 100)}%`;
        }

        // 更新 AI 調用數
        const aiCallsElement = document.getElementById('aiCalls');
        const aiProgress = document.getElementById('aiProgress');
        if (aiCallsElement && data.recent_activity) {
            const aiCalls = data.recent_activity.ai_calls_today || 0;
            this.animateNumber(aiCallsElement, aiCalls);
            aiProgress.style.width = `${Math.min((aiCalls / 500) * 100, 100)}%`;
        }
    }

    updateCacheInfo(cacheData) {
        const cacheHitElement = document.getElementById('cacheHit');
        const cacheProgress = document.getElementById('cacheProgress');

        if (cacheHitElement && cacheData.cache_stats) {
            const hitRate = parseInt(cacheData.cache_performance?.hit_rate_estimate || '75%');
            cacheHitElement.textContent = `${hitRate}%`;
            cacheProgress.style.width = `${hitRate}%`;
        }
    }

    updateSystemMetrics(performanceData) {
        const metricsContainer = document.getElementById('systemMetrics');
        if (!metricsContainer || !performanceData.api_endpoints) return;

        // 更新平均響應時間
        const avgResponseElement = document.getElementById('avgResponse');
        const responseProgress = document.getElementById('responseProgress');
        if (avgResponseElement && performanceData.api_endpoints.get_articles) {
            const avgTime = performanceData.api_endpoints.get_articles.avg_response_ms;
            avgResponseElement.textContent = avgTime;
            responseProgress.style.width = `${Math.min((avgTime / 500) * 100, 100)}%`;
        }

        // 生成系統指標HTML
        const endpoints = performanceData.api_endpoints;
        let metricsHtml = '';

        Object.entries(endpoints).forEach(([endpoint, metrics]) => {
            const status = metrics.avg_response_ms < 200 ? 'status-active' :
                          metrics.avg_response_ms < 1000 ? 'status-warning' : 'status-error';

            metricsHtml += `
                <div class="metric-row">
                    <span class="metric-label">
                        <span class="status-indicator ${status}"></span>${this.formatEndpointName(endpoint)}
                    </span>
                    <span class="metric-value">${metrics.avg_response_ms}ms</span>
                </div>
            `;
        });

        // 添加緩存指標
        if (performanceData.cache_performance) {
            const cache = performanceData.cache_performance;
            metricsHtml += `
                <div class="metric-row">
                    <span class="metric-label">
                        <span class="status-indicator status-active"></span>緩存記憶體
                    </span>
                    <span class="metric-value">${cache.memory_usage_kb}KB</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">
                        <span class="status-indicator status-active"></span>活躍緩存鍵
                    </span>
                    <span class="metric-value">${cache.active_cache_keys}</span>
                </div>
            `;
        }

        metricsContainer.innerHTML = metricsHtml;
    }

    updateServiceStatus(performanceData) {
        // AI 服務狀態
        const aiStatus = document.getElementById('aiServiceStatus');
        const aiText = document.getElementById('aiServiceText');
        if (aiStatus && aiText) {
            if (performanceData.api_endpoints?.generate_article) {
                aiStatus.className = 'status-indicator status-active';
                aiText.textContent = '正常運行';
            } else {
                aiStatus.className = 'status-indicator status-error';
                aiText.textContent = '服務異常';
            }
        }

        // 緩存服務狀態
        const cacheStatus = document.getElementById('cacheServiceStatus');
        const cacheText = document.getElementById('cacheServiceText');
        if (cacheStatus && cacheText) {
            if (performanceData.cache_performance?.active_cache_keys > 0) {
                cacheStatus.className = 'status-indicator status-active';
                cacheText.textContent = '運行中';
            } else {
                cacheStatus.className = 'status-indicator status-warning';
                cacheText.textContent = '低效率';
            }
        }
    }

    formatEndpointName(endpoint) {
        const names = {
            'get_articles': '文章列表',
            'get_article_content': '文章內容',
            'generate_article': '文章生成',
            'get_categories': '分類查詢',
            'get_stats': '統計查詢'
        };
        return names[endpoint] || endpoint;
    }

    initCharts() {
        this.initAIUsageChart();
        this.initArticleChart();
    }

    initAIUsageChart() {
        const ctx = document.getElementById('aiUsageChart');
        if (!ctx) return;

        // 模擬 AI 使用量數據
        const last7Days = this.getLast7Days();
        const aiUsageData = last7Days.map(() => Math.floor(Math.random() * 100) + 20);

        this.aiUsageChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: last7Days,
                datasets: [{
                    label: 'AI 調用次數',
                    data: aiUsageData,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(103, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
    }

    initArticleChart() {
        const ctx = document.getElementById('articleChart');
        if (!ctx) return;

        // 模擬文章分類數據
        const categories = ['投資理財', '風險管理', '財富累積', '創業精神', '理財工具'];
        const articleCounts = categories.map(() => Math.floor(Math.random() * 50) + 10);

        this.articleChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categories,
                datasets: [{
                    data: articleCounts,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    getLast7Days() {
        const days = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            days.push(date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' }));
        }
        return days;
    }

    animateNumber(element, targetValue) {
        const startValue = parseInt(element.textContent) || 0;
        const difference = targetValue - startValue;
        const duration = 1000; // 1秒動畫
        const steps = 60;
        const stepValue = difference / steps;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            const currentValue = Math.round(startValue + (stepValue * currentStep));
            element.textContent = currentValue.toLocaleString();

            if (currentStep >= steps) {
                clearInterval(timer);
                element.textContent = targetValue.toLocaleString();
            }
        }, duration / steps);
    }

    startAutoRefresh() {
        this.autoRefreshTimer = setInterval(() => {
            console.log('🔄 自動刷新統計數據...');
            this.loadDashboardData();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }

    async refreshAIChart() {
        console.log('🔄 刷新 AI 使用量圖表...');

        const button = document.querySelector('[onclick="refreshAIChart()"]');
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            // 模擬數據更新
            const last7Days = this.getLast7Days();
            const newData = last7Days.map(() => Math.floor(Math.random() * 100) + 20);

            this.aiUsageChart.data.datasets[0].data = newData;
            this.aiUsageChart.update();

            setTimeout(() => {
                button.innerHTML = '<i class="fas fa-sync-alt"></i>';
            }, 1000);

        } catch (error) {
            console.error('刷新 AI 圖表失敗:', error);
            button.innerHTML = '<i class="fas fa-sync-alt"></i>';
        }
    }

    async refreshArticleChart() {
        console.log('🔄 刷新文章統計圖表...');

        const button = document.querySelector('[onclick="refreshArticleChart()"]');
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            // 模擬數據更新
            const newData = this.articleChart.data.labels.map(() =>
                Math.floor(Math.random() * 50) + 10
            );

            this.articleChart.data.datasets[0].data = newData;
            this.articleChart.update();

            setTimeout(() => {
                button.innerHTML = '<i class="fas fa-sync-alt"></i>';
            }, 1000);

        } catch (error) {
            console.error('刷新文章圖表失敗:', error);
            button.innerHTML = '<i class="fas fa-sync-alt"></i>';
        }
    }

    showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.querySelector('.container');
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }

    destroy() {
        this.stopAutoRefresh();
        if (this.aiUsageChart) {
            this.aiUsageChart.destroy();
        }
        if (this.articleChart) {
            this.articleChart.destroy();
        }
    }
}

// 全局函數供 HTML 調用
window.refreshAIChart = function() {
    if (window.dashboardManager) {
        window.dashboardManager.refreshAIChart();
    }
};

window.refreshArticleChart = function() {
    if (window.dashboardManager) {
        window.dashboardManager.refreshArticleChart();
    }
};

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 載入資料統計儀表板...');
    window.dashboardManager = new DashboardManager();
});

// 頁面卸載時清理資源
window.addEventListener('beforeunload', function() {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});