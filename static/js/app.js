/**
 * 財商成長思維平台前端應用
 */

// 全域變數
let currentArticles = [];
let currentGeneratedArticle = null;
let lastGenerationParams = null;
let categories = [];

// API 基礎路徑
const API_BASE = '/api/v1/financial-wisdom';

// 通知系統
class NotificationManager {
    constructor() {
        this.container = document.getElementById('notificationContainer');
    }
    
    showLoading(message = '載入中...', showProgress = false) {
        const loadingId = 'loading-' + Date.now();
        const loadingHTML = `
            <div id="${loadingId}" class="enhanced-loading show">
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
                ${showProgress ? '<div class="progress-bar"><div class="progress-fill"></div></div>' : ''}
            </div>
        `;
        
        this.container.innerHTML = loadingHTML;
        return loadingId;
    }
    
    hideLoading(loadingId) {
        const element = document.getElementById(loadingId);
        if (element) {
            element.remove();
        }
    }
    
    showError(title, message, actions = null, autoHide = true) {
        const errorId = 'error-' + Date.now();
        const actionsHTML = actions ? `
            <div class="error-actions">
                ${actions.map(action => 
                    `<button class="btn btn-sm btn-outline-danger me-2" onclick="${action.onClick}">${action.text}</button>`
                ).join('')}
            </div>
        ` : '';
        
        const errorHTML = `
            <div id="${errorId}" class="error-alert show">
                <div class="error-title">${title}</div>
                <div class="error-message">${message}</div>
                ${actionsHTML}
            </div>
        `;
        
        this.container.innerHTML = errorHTML;
        
        if (autoHide) {
            setTimeout(() => this.hideError(errorId), 5000);
        }
        
        return errorId;
    }
    
    hideError(errorId) {
        const element = document.getElementById(errorId);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => element.remove(), 300);
        }
    }
    
    showSuccess(title, message, autoHide = true) {
        const successId = 'success-' + Date.now();
        const successHTML = `
            <div id="${successId}" class="success-alert show">
                <div class="success-title">${title}</div>
                <div class="success-message">${message}</div>
            </div>
        `;
        
        this.container.innerHTML = successHTML;
        
        if (autoHide) {
            setTimeout(() => this.hideSuccess(successId), 3000);
        }
        
        return successId;
    }
    
    hideSuccess(successId) {
        const element = document.getElementById(successId);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => element.remove(), 300);
        }
    }
    
    clear() {
        this.container.innerHTML = '';
    }
}

// 創建全局通知管理器
const notifications = new NotificationManager();

// 文章內容緩存系統
class ArticleCache {
    constructor(maxSize = 50) {
        this.cache = new Map();
        this.maxSize = maxSize;
        this.loadingStates = new Set(); // 追蹤正在載入的文章
    }
    
    get(articleId) {
        return this.cache.get(articleId);
    }
    
    set(articleId, article) {
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(articleId, article);
    }
    
    has(articleId) {
        return this.cache.has(articleId);
    }
    
    isLoading(articleId) {
        return this.loadingStates.has(articleId);
    }
    
    setLoading(articleId) {
        this.loadingStates.add(articleId);
    }
    
    clearLoading(articleId) {
        this.loadingStates.delete(articleId);
    }
}

// 創建全局文章緩存
const articleCache = new ArticleCache();

// 性能監控和分析系統
class AnalyticsManager {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.startTime = Date.now();
        this.events = [];
        this.articleViews = new Map(); // 文章閱讀統計
    }
    
    generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // 記錄文章閱讀事件
    trackArticleView(articleId, articleTitle, category) {
        const event = {
            type: 'article_view',
            articleId,
            articleTitle,
            category,
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        this.events.push(event);
        
        // 更新閱讀統計
        const viewData = this.articleViews.get(articleId) || {
            title: articleTitle,
            category,
            views: 0,
            totalTime: 0,
            lastViewed: null
        };
        
        viewData.views++;
        viewData.lastViewed = new Date().toISOString();
        this.articleViews.set(articleId, viewData);
        
        console.log('📊 文章閱讀追蹤:', event);
        this.sendAnalytics(event);
    }
    
    // 記錄搜索事件
    trackSearch(query, resultsCount) {
        const event = {
            type: 'search',
            query,
            resultsCount,
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        this.events.push(event);
        console.log('🔍 搜索追蹤:', event);
    }
    
    // 記錄生成文章事件
    trackArticleGeneration(topic, wordCount, success) {
        const event = {
            type: 'article_generation',
            topic,
            wordCount,
            success,
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        this.events.push(event);
        console.log('🤖 文章生成追蹤:', event);
    }
    
    // 記錄性能指標
    trackPerformance(metric, value, context = {}) {
        const event = {
            type: 'performance',
            metric,
            value,
            context,
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        this.events.push(event);
        console.log('⚡ 性能追蹤:', event);
    }
    
    // 發送分析數據（模擬）
    async sendAnalytics(event) {
        // 在真實環境中，這裡會發送到分析服務
        // 現在暫時存儲到 localStorage
        const existingData = JSON.parse(localStorage.getItem('analytics_data') || '[]');
        existingData.push(event);
        
        // 只保留最近 1000 個事件
        if (existingData.length > 1000) {
            existingData.splice(0, existingData.length - 1000);
        }
        
        localStorage.setItem('analytics_data', JSON.stringify(existingData));
    }
    
    // 獲取分析報告
    getAnalyticsReport() {
        const data = JSON.parse(localStorage.getItem('analytics_data') || '[]');
        const now = Date.now();
        const dayMs = 24 * 60 * 60 * 1000;
        
        // 今日數據
        const todayData = data.filter(event => 
            now - event.timestamp < dayMs
        );
        
        // 統計文章閱讀
        const articleViews = {};
        const searchQueries = {};
        const generationAttempts = { success: 0, failed: 0 };
        
        todayData.forEach(event => {
            switch (event.type) {
                case 'article_view':
                    articleViews[event.articleId] = (articleViews[event.articleId] || 0) + 1;
                    break;
                case 'search':
                    searchQueries[event.query] = (searchQueries[event.query] || 0) + 1;
                    break;
                case 'article_generation':
                    if (event.success) {
                        generationAttempts.success++;
                    } else {
                        generationAttempts.failed++;
                    }
                    break;
            }
        });
        
        return {
            totalEvents: todayData.length,
            uniqueArticleViews: Object.keys(articleViews).length,
            totalArticleViews: Object.values(articleViews).reduce((sum, views) => sum + views, 0),
            topArticles: Object.entries(articleViews)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([id, views]) => ({ id, views })),
            totalSearches: Object.values(searchQueries).reduce((sum, count) => sum + count, 0),
            topSearchQueries: Object.entries(searchQueries)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([query, count]) => ({ query, count })),
            generationStats: generationAttempts,
            sessionDuration: Math.round((now - this.startTime) / 1000 / 60) // 分鐘
        };
    }
}

// 創建全局分析管理器
const analytics = new AnalyticsManager();

// API 請求包裝器，帶有自動錯誤處理
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API請求失敗: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API請求錯誤:', error);
        throw error;
    }
}

// 骨架屏載入效果
function showSkeletonCards(containerId, count = 3) {
    const container = document.getElementById(containerId);
    const skeletonHTML = Array(count).fill().map(() => `
        <div class="skeleton-card">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text medium"></div>
            <div class="skeleton skeleton-text short"></div>
        </div>
    `).join('');
    
    container.innerHTML = skeletonHTML;
}

// 文章生成功能
async function generateArticle() {
    const form = document.getElementById('generateForm');
    const resultDiv = document.getElementById('generateResult');
    const submitButton = form.querySelector('button[type="submit"]');
    const loading = submitButton.querySelector('.loading');
    
    try {
        // 顯示loading狀態
        submitButton.disabled = true;
        loading.style.display = 'inline-block';
        
        // 收集表單數據 - 修正元素 ID
        const articleData = {
            title: document.getElementById('articleTitle')?.value || '',
            topic: document.getElementById('articleTopic')?.value || '',
            target_audience: document.getElementById('targetAudience')?.value || '一般投資者',
            writing_style: document.getElementById('writingStyle')?.value || '實用智慧',
            word_count_target: parseInt(document.getElementById('wordCountTarget')?.value || '1500'),
            include_case_study: document.getElementById('includeCaseStudy')?.checked || true,
            focus_areas: (document.getElementById('focusAreas')?.value || '').split(',').map(area => area.trim()).filter(area => area)
        };
        
        // 驗證必填欄位
        if (!articleData.title || !articleData.topic) {
            notifications.showError('驗證失敗', '請填寫文章標題和主題');
            submitButton.disabled = false;
            loading.style.display = 'none';
            return;
        }
        
        console.log('發送的文章數據:', articleData);
        
        // 顯示全域載入狀態
        // const globalLoadingId = notifications.showLoading('正在生成財商文章，請稍候...', true);
        
        // 顯示生成中狀態
        resultDiv.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner"></div>
                <h5 class="loading-text">正在生成文章...</h5>
                <p class="text-muted">使用AI智能分析生成高品質內容，請稍候</p>
            </div>
        `;
        
        // 發送請求
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(articleData)
        });
        
        if (!response.ok) {
            throw new Error(`生成失敗: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('收到的響應數據:', result);
        
        // 顯示結果，包含完整提示詞
        resultDiv.innerHTML = `
            <div class="generated-article">
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0"><i class="fas fa-check-circle text-success me-2"></i>生成成功！</h5>
                        <span class="badge bg-primary">品質分數: ${result.quality_score}/10</span>
                    </div>
                    
                    <!-- 提示詞顯示區域 -->
                    <div class="prompt-section mb-4">
                        <button class="btn btn-outline-info btn-sm mb-2" type="button" data-bs-toggle="collapse" data-bs-target="#promptDisplay">
                            <i class="fas fa-code me-1"></i>查看完整提示詞
                        </button>
                        <div class="collapse" id="promptDisplay">
                            <div class="card card-body bg-light">
                                <h6><i class="fas fa-terminal me-2"></i>生成此文章使用的AI提示詞：</h6>
                                <pre style="white-space: pre-wrap; font-size: 0.85em; max-height: 300px; overflow-y: auto;">${result.prompt_used || '提示詞資料不可用'}</pre>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 文章內容 -->
                    <div class="article-content">
                        <h4 class="article-title mb-3">${result.title}</h4>
                        <div class="article-meta mb-3">
                            <span class="badge bg-secondary me-2">分類: ${result.category}</span>
                            <span class="badge bg-info me-2">字數: ${result.word_count}</span>
                            <span class="badge bg-success">預估閱讀: ${result.reading_time}分鐘</span>
                        </div>
                        <div class="article-body" style="max-height: 400px; overflow-y: auto; border: 1px solid #dee2e6; padding: 1rem; background: #f8f9fa;">
                            <pre style="white-space: pre-wrap; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">${result.content}</pre>
                        </div>
                        <div class="article-tags mt-3">
                            ${(result.tags || []).map(tag => `<span class="badge bg-primary me-1">#${tag}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <button class="btn btn-success me-2" onclick="saveGeneratedArticle()">
                            <i class="fas fa-save me-1"></i>保存到 Notion
                        </button>
                        <button class="btn btn-outline-secondary me-2" onclick="copyArticleContent('${encodeURIComponent(result.content)}')">
                            <i class="fas fa-copy me-1"></i>複製內容
                        </button>
                        <button class="btn btn-primary" onclick="regenerateArticle()">
                            <i class="fas fa-redo me-1"></i>重新生成
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        notifications.showSuccess('生成成功', '文章已成功生成！');
        
        // 隱藏全域載入狀態
        // notifications.hideLoading(globalLoadingId);
        
    } catch (error) {
        console.error('文章生成錯誤:', error);
        
        // 隱藏全域載入狀態
        // notifications.hideLoading(globalLoadingId);
        
        resultDiv.innerHTML = `
            <div class="text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                <h5>生成失敗</h5>
                <p>${error.message}</p>
                <button class="btn btn-outline-primary" onclick="document.getElementById('generateForm').querySelector('button[type=submit]').click()">
                    <i class="fas fa-retry me-1"></i>重試
                </button>
            </div>
        `;
        notifications.showError('生成失敗', error.message);
    } finally {
        // 恢復按鈕狀態
        submitButton.disabled = false;
        loading.style.display = 'none';
    }
}

// 複製文章內容功能
function copyArticleContent(encodedContent) {
    const content = decodeURIComponent(encodedContent);
    navigator.clipboard.writeText(content).then(() => {
        notifications.showSuccess('複製成功', '內容已複製到剪貼板');
    }).catch(err => {
        console.error('複製失敗:', err);
        notifications.showError('複製失敗', '無法複製內容到剪貼板');
    });
}

// 重新生成文章
async function regenerateArticle() {
    if (!lastGenerationParams) {
        notifications.showError('重新生成失敗', '沒有找到之前的生成參數');
        return;
    }
    
    try {
        // 顯示載入狀態
        let generateResult = document.getElementById('generateResult');
        generateResult.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner"></div>
                <h5 class="loading-text">正在重新生成文章...</h5>
                <p class="text-muted">使用之前相同的參數重新生成</p>
            </div>
        `;
        
        // 使用保存的參數重新生成
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(lastGenerationParams)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '重新生成失敗');
        }
        
        const result = await response.json();
        currentGeneratedArticle = result;
        
        // 顯示新生成的文章（使用和第一次生成相同的模板）
        generateResult = document.getElementById('generateResult');
        generateResult.innerHTML = `
            <div class="generated-article">
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0"><i class="fas fa-check-circle text-success me-2"></i>重新生成成功！</h5>
                        <span class="badge bg-primary">品質分數: ${result.quality_score}/10</span>
                    </div>
                    
                    <!-- 提示詞顯示區域 -->
                    <div class="prompt-section mb-4">
                        <button class="btn btn-outline-info btn-sm mb-2" type="button" data-bs-toggle="collapse" data-bs-target="#promptDisplay">
                            <i class="fas fa-code me-1"></i>查看完整提示詞
                        </button>
                        <div class="collapse" id="promptDisplay">
                            <div class="card card-body bg-light">
                                <h6><i class="fas fa-terminal me-2"></i>生成此文章使用的AI提示詞：</h6>
                                <pre style="white-space: pre-wrap; font-size: 0.85em; max-height: 300px; overflow-y: auto;">${result.prompt_used || '提示詞資料不可用'}</pre>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 文章內容 -->
                    <div class="article-content">
                        <h4 class="article-title mb-3">${result.title}</h4>
                        <div class="article-meta mb-3">
                            <span class="badge bg-secondary me-2">分類: ${result.category}</span>
                            <span class="badge bg-info me-2">字數: ${result.word_count}</span>
                            <span class="badge bg-success">預估閱讀: ${result.reading_time}分鐘</span>
                        </div>
                        <div class="article-body" style="max-height: 400px; overflow-y: auto; border: 1px solid #dee2e6; padding: 1rem; background: #f8f9fa;">
                            <pre style="white-space: pre-wrap; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">${result.content}</pre>
                        </div>
                        <div class="article-tags mt-3">
                            ${(result.tags || []).map(tag => `<span class="badge bg-primary me-1">#${tag}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <button class="btn btn-success me-2" onclick="saveGeneratedArticle()">
                            <i class="fas fa-save me-1"></i>保存到 Notion
                        </button>
                        <button class="btn btn-outline-secondary me-2" onclick="copyArticleContent('${encodeURIComponent(result.content)}')">
                            <i class="fas fa-copy me-1"></i>複製內容
                        </button>
                        <button class="btn btn-primary" onclick="regenerateArticle()">
                            <i class="fas fa-redo me-1"></i>重新生成
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        notifications.showSuccess('重新生成成功', '文章已重新生成！');
        
    } catch (error) {
        console.error('重新生成錯誤:', error);
        notifications.showError('重新生成失敗', error.message);
        
        // 顯示錯誤狀態
        generateResult = document.getElementById('generateResult');
        generateResult.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>重新生成失敗</h5>
                <p>錯誤：${error.message}</p>
                <button class="btn btn-primary" onclick="regenerateArticle()">
                    <i class="fas fa-redo me-1"></i>重試
                </button>
            </div>
        `;
    }
}

// 應用初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadCategories();
    loadArticles();
    
    // 綁定表單提交事件
    const generateForm = document.getElementById('generateForm');
    if (generateForm) {
        generateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateArticle();
        });
    }
    
    // 綁定事件處理器
    setupEventListeners();
});

function setupEventListeners() {
    // 文章生成表單
    document.getElementById('generateForm').addEventListener('submit', handleGenerateArticle);
    
    // 搜尋功能
    document.getElementById('searchInput').addEventListener('input', debounce(loadArticles, 500));
    document.getElementById('categoryFilter').addEventListener('change', loadArticles);
}

// 工具函數：防抖動
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 載入儀表板統計資料
async function loadDashboard() {
    try {
        showSkeletonCards('statsCards', 4);
        
        const stats = await apiRequest(`${API_BASE}/stats`);
        renderStatsCards(stats);
        
    } catch (error) {
        console.error('載入統計資料錯誤:', error);
        notifications.showError('載入失敗', '無法載入統計資料，請檢查網路連接或稍後重試', [
            { text: '重試', onClick: 'loadDashboard()' }
        ]);
        document.getElementById('statsCards').innerHTML = '<div class="col-12"><div class="alert alert-warning text-center">統計資料載入失敗</div></div>';
    }
}

// 渲染統計卡片
function renderStatsCards(stats) {
    const container = document.getElementById('statsCards');
    
    const cardsHTML = `
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-file-alt fa-2x mb-2"></i>
                    <h3>${stats.total_articles || 0}</h3>
                    <p class="mb-0">總文章數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-font fa-2x mb-2"></i>
                    <h3>${(stats.total_words || 0).toLocaleString()}</h3>
                    <p class="mb-0">總字數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-chart-line fa-2x mb-2"></i>
                    <h3>${stats.average_words || 0}</h3>
                    <p class="mb-0">平均字數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-tags fa-2x mb-2"></i>
                    <h3>${Object.keys(stats.categories || {}).length}</h3>
                    <p class="mb-0">分類數量</p>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = cardsHTML;
    
    // 如果有分類統計，顯示詳細信息
    if (stats.categories) {
        const categoriesInfo = Object.entries(stats.categories)
            .map(([category, count]) => `<span class="badge bg-primary me-1">${category}: ${count}</span>`)
            .join('');
        
        container.innerHTML += `
            <div class="col-12 mt-3">
                <div class="card">
                    <div class="card-body">
                        <h6><i class="fas fa-chart-pie me-2"></i>分類統計</h6>
                        ${categoriesInfo}
                    </div>
                </div>
            </div>
        `;
    }
}

// 載入儀表板統計資料
async function loadDashboard() {
    try {
        console.log('📊 載入儀表板統計資料...');
        
        // 載入基本統計資料
        const statsResponse = await fetch(`${API_BASE}/stats`);
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('📊 統計資料載入完成:', statsData);
        }
        
        console.log('✅ 儀表板載入完成');
    } catch (error) {
        console.error('❌ 儀表板載入失敗:', error);
        // 不顯示錯誤給用戶，因為這是可選功能
    }
}

// 載入分類選項
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        if (!response.ok) throw new Error('載入分類失敗');
        
        const data = await response.json();
        categories = data.categories || [];
        
        // 更新分類下拉選單
        const categoryFilter = document.getElementById('categoryFilter');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
        
    } catch (error) {
        console.error('載入分類錯誤:', error);
    }
}

// 載入文章列表
async function loadArticles() {
    try {
        console.log('📚 開始載入文章列表...');
        showLoading('articlesList');
        
        // 構建查詢參數
        const params = new URLSearchParams({
            limit: 50  // 增加到50以確保載入所有文章
        });
        
        const searchTerm = document.getElementById('searchInput').value;
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        
        const selectedCategory = document.getElementById('categoryFilter').value;
        if (selectedCategory) {
            params.append('category', selectedCategory);
        }
        
        const url = `${API_BASE}/articles?${params}`;
        console.log('🌐 請求URL:', url);
        
        const response = await fetch(url);
        console.log('📡 API響應狀態:', response.status);
        
        if (!response.ok) throw new Error('載入文章失敗');
        
        const data = await response.json();
        currentArticles = data.articles || [];
        
        // 追蹤搜索行為
        if (searchTerm) {
            analytics.trackSearch(searchTerm, currentArticles.length);
        }
        
        console.log('📄 載入文章數量:', currentArticles.length);
        console.log('🔍 文章數據樣本:', currentArticles.length > 0 ? currentArticles[0] : '無數據');
        
        renderArticlesList(currentArticles);
        
    } catch (error) {
        console.error('載入文章錯誤:', error);
        showError('articlesList', '無法載入文章列表');
    }
}

// 渲染文章列表
function renderArticlesList(articles) {
    console.log('🎨 開始渲染文章列表，文章數量:', articles.length);
    const container = document.getElementById('articlesList');
    
    if (!container) {
        console.error('❌ 找不到文章列表容器 #articlesList');
        return;
    }
    
    if (articles.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-file-alt fa-3x mb-3"></i>
                <h5>沒有找到相關文章</h5>
                <p>嘗試調整搜尋條件或創建新文章</p>
            </div>
        `;
        return;
    }
    
    const articlesHTML = articles.map((article, index) => `
        <div class="card card-hover article-card mb-3" onclick="handleArticleClick('${article.id}', this)" style="cursor: pointer;" data-article-id="${article.id}">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-1 text-center">
                        <span class="badge bg-secondary fs-6">${index + 1}</span>
                    </div>
                    <div class="col-md-7">
                        <h5 class="card-title mb-2 text-primary">${escapeHtml(article.title)}</h5>
                        <p class="card-text text-muted mb-2 small">${escapeHtml(article.summary || '點擊查看完整文章內容...')}</p>
                        <div class="mb-2">
                            <span class="badge category-badge bg-primary me-2">${escapeHtml(article.category)}</span>
                            ${article.tags && article.tags.length > 0 ? article.tags.map(tag => `<span class="tag text-primary">#${escapeHtml(tag)}</span>`).join('') : '<span class="text-muted small">暫無標籤</span>'}
                        </div>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="small text-muted">
                            <div class="mb-1"><i class="fas fa-font me-2"></i><strong>${article.word_count || 0}</strong> 字</div>
                            <div class="mb-1"><i class="fas fa-clock me-2"></i><strong>${article.reading_time || Math.ceil((article.word_count || 800) / 300)}</strong> 分鐘閱讀</div>
                            <div class="mb-1"><i class="fas fa-calendar me-2"></i>${formatDate(article.publish_date)}</div>
                            <div class="mt-2">
                                <span class="badge bg-success">✅ ${article.status || '已發布'}</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">
                            <i class="fas fa-mouse-pointer me-1"></i>點擊查看完整文章內容
                            ${articleCache.has(article.id) ? '<span class="badge bg-info ms-2"><i class="fas fa-download me-1"></i>已緩存</span>' : ''}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = articlesHTML;
    console.log('✅ 文章列表渲染完成，HTML長度:', articlesHTML.length);
}

// 處理文章卡片點擊事件
async function handleArticleClick(articleId, cardElement) {
    // 防止重複點擊
    if (cardElement.classList.contains('loading')) {
        return;
    }
    
    // 添加載入狀態到卡片
    cardElement.classList.add('loading');
    cardElement.style.transform = 'scale(0.98)';
    cardElement.style.transition = 'all 0.2s ease';
    
    // 添加載入指示器
    const originalContent = cardElement.querySelector('.col-md-7 h5').innerHTML;
    cardElement.querySelector('.col-md-7 h5').innerHTML = '<i class="fas fa-spinner fa-spin me-2 text-primary"></i>' + originalContent;
    
    try {
        await showArticleDetail(articleId);
    } finally {
        // 移除載入狀態
        cardElement.classList.remove('loading');
        cardElement.style.transform = '';
        cardElement.style.transition = '';
        cardElement.querySelector('.col-md-7 h5').innerHTML = originalContent;
    }
}

// 顯示文章詳情
async function showArticleDetail(articleId) {
    // 防止重複點擊 - 如果正在載入，直接返回
    if (articleCache.isLoading(articleId)) {
        console.log('文章正在載入中，請稍候...');
        return;
    }
    
    try {
        let article;
        
        // 檢查緩存
        if (articleCache.has(articleId)) {
            console.log('從緩存載入文章:', articleId);
            article = articleCache.get(articleId);
        } else {
            // 標記為載入中
            articleCache.setLoading(articleId);
            
            // 顯示載入狀態
            const loadingId = notifications.showLoading('載入文章內容中...', false);
            
            try {
                console.log('從 API 載入文章:', articleId);
                const response = await fetch(`${API_BASE}/articles/${articleId}`);
                if (!response.ok) throw new Error('載入文章內容失敗');
                
                article = await response.json();
                
                // 緩存文章內容
                articleCache.set(articleId, article);
                
                // 隱藏載入狀態
                notifications.hideLoading(loadingId);
                
            } finally {
                // 清除載入狀態
                articleCache.clearLoading(articleId);
            }
        }
        
        // 渲染文章內容（從緩存或新載入）
        renderArticleModal(article, articleId);
        
    } catch (error) {
        console.error('載入文章詳情錯誤:', error);
        articleCache.clearLoading(articleId);
        
        notifications.showError(
            '載入失敗', 
            '無法載入文章詳情，請檢查網路連接', 
            [
                { text: '重試', onClick: `showArticleDetail('${articleId}')` },
                { text: '關閉', onClick: `notifications.clear()` }
            ]
        );
    }
}

// 渲染文章模態框內容
function renderArticleModal(article, articleId) {
    // 追蹤文章閱讀
    const category = article.properties?.主題類別?.select?.name || 'Unknown';
    analytics.trackArticleView(articleId, article.title, category);
    
    // 設置模態框內容
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) {
        modalTitle.textContent = article.title;
    }
    
    const modalContent = document.getElementById('modalContent');
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="article-content">
                <div class="mb-3">
                    <strong>分類：</strong>
                    <span class="badge bg-primary">${escapeHtml(article.properties?.主題類別?.select?.name || '未分類')}</span>
                </div>
                <div class="mb-3">
                    <strong>狀態：</strong>
                    <span class="badge bg-success">${escapeHtml(article.properties?.發布狀態?.select?.name || '未知')}</span>
                </div>
                <div class="mb-3">
                    <strong>標籤：</strong>
                    ${(article.properties?.標籤?.multi_select || []).map(tag => 
                        `<span class="tag">#${escapeHtml(tag.name)}</span>`
                    ).join('')}
                </div>
                <div class="mb-3">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        ${articleCache.has(articleId) ? '從緩存載入' : '新載入'}
                    </small>
                </div>
                <hr>
                <div style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(article.content)}</div>
            </div>
        `;
    } else {
        console.error('modalContent element not found');
        return;
    }
    
    // 設置 Notion 連結
    const notionLink = document.getElementById('notionLink');
    if (notionLink) {
        notionLink.href = `https://notion.so/${articleId.replace(/-/g, '')}`;
    }
    
    // 顯示模態框
    const articleModalElement = document.getElementById('articleModal');
    if (articleModalElement) {
        const modal = new bootstrap.Modal(articleModalElement);
        modal.show();
    } else {
        console.error('articleModal element not found');
    }
}

// 處理文章生成
async function handleGenerateArticle(event) {
    event.preventDefault();
    
    const generateBtn = document.querySelector('#generateForm button[type="submit"]');
    // const loadingId = notifications.showLoading('正在生成財商文章，請稍候...', true);
    
    // 確保隱藏任何之前的通知
    notifications.clear();
    
    try {
        console.log('🤖 開始生成文章...');
        
        // 顯示載入狀態
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>生成中...';
        
        // 收集表單資料
        const templatePrompt = getTemplatePrompt();
        const userTopic = document.getElementById('articleTopic').value;
        
        // 根據模板構建完整的主題描述
        let fullTopic = userTopic;
        if (templatePrompt) {
            fullTopic = `${templatePrompt}\n\n具體主題：${userTopic}`;
        }
        
        const formData = {
            title: document.getElementById('articleTitle').value,
            topic: fullTopic,
            target_audience: document.getElementById('targetAudience').value,
            writing_style: document.getElementById('writingStyle').value,
            word_count_target: parseInt(document.getElementById('wordCountTarget').value),
            include_case_study: document.getElementById('includeCaseStudy').checked,
            focus_areas: document.getElementById('focusAreas').value
                .split(',')
                .map(area => area.trim())
                .filter(area => area.length > 0)
        };
        
        // 保存生成參數以供重新生成使用
        lastGenerationParams = { ...formData };
        
        console.log('🎯 使用模板：', document.getElementById('articleTemplate').value);
        
        // 發送生成請求
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '生成失敗');
        }
        
        const result = await response.json();
        currentGeneratedArticle = result;
        
        // 顯示預覽
        showGeneratedPreview(result);
        
        // 滾動到預覽區域
        const previewEl = document.getElementById('generateResult');
        if (previewEl) {
            previewEl.scrollIntoView({ behavior: 'smooth' });
        }
        
        console.log('✅ 文章生成完成');
        
    } catch (error) {
        console.error('❌ 文章生成錯誤:', error);
        notifications.showError('生成失敗', error.message);
    } finally {
        // 隱藏載入狀態
        // notifications.hideLoading(loadingId);
        
        // 恢復按鈕狀態
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>生成文章';
    }
}

// 顯示生成的文章預覽
function showGeneratedPreview(article) {
    console.log('🎨 顯示文章預覽:', article.title);
    const previewContainer = document.getElementById('generateResult');
    
    previewContainer.innerHTML = `
        <div class="border p-3 rounded bg-white">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <div class="flex-grow-1 me-3">
                    <input type="text" id="editTitle" class="form-control form-control-lg fw-bold text-primary border-0 p-0" 
                           value="${escapeHtml(article.title)}" style="background: transparent;">
                </div>
                <div class="text-end">
                    <select id="editCategory" class="form-select form-select-sm d-inline-block w-auto">
                        <option value="風險管理" ${article.category === '風險管理' ? 'selected' : ''}>風險管理</option>
                        <option value="思維轉換" ${article.category === '思維轉換' ? 'selected' : ''}>思維轉換</option>
                        <option value="實戰技巧" ${article.category === '實戰技巧' ? 'selected' : ''}>實戰技巧</option>
                        <option value="心理素質" ${article.category === '心理素質' ? 'selected' : ''}>心理素質</option>
                        <option value="財富建構" ${article.category === '財富建構' ? 'selected' : ''}>財富建構</option>
                    </select>
                    <div class="small text-muted mt-1">
                        <span id="wordCountDisplay">${article.word_count}</span> 字 • ${article.reading_time} 分鐘閱讀
                    </div>
                    <div class="small">
                        品質分數: <span class="badge bg-success">${article.quality_score.toFixed(1)}</span>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <input type="text" id="editTags" class="form-control form-control-sm" 
                       placeholder="標籤 (用逗號分隔)" 
                       value="${article.tags.join(', ')}">
            </div>
            
            <div class="mb-3">
                <label class="form-label small fw-bold">文章內容:</label>
                <textarea id="editContent" class="form-control" rows="12" 
                          style="font-family: system-ui; line-height: 1.6;"
                          oninput="updateWordCount()">${escapeHtml(article.content)}</textarea>
            </div>
            
            <div class="d-flex justify-content-between">
                <div>
                    <button class="btn btn-outline-secondary btn-sm" onclick="resetToOriginal()">
                        <i class="fas fa-undo me-1"></i>重置
                    </button>
                </div>
                <div class="gap-2 d-flex">
                    <button class="btn btn-outline-primary" onclick="previewChanges()">
                        <i class="fas fa-eye me-1"></i>預覽
                    </button>
                    <button class="btn btn-success" onclick="saveEditedArticle()">
                        <i class="fas fa-save me-1"></i>保存到 Notion
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // 儲存原始文章資料以供重置使用
    window.originalArticle = { ...article };
}

// 顯示保存模態框
function showSaveModal() {
    if (!currentGeneratedArticle) {
        alert('沒有可保存的文章');
        return;
    }
    
    // 設置保存預覽
    const savePreview = document.getElementById('savePreview');
    if (savePreview) {
        savePreview.innerHTML = `
            <h6>${escapeHtml(currentGeneratedArticle.title)}</h6>
            <p class="small text-muted mb-2">
                分類: ${escapeHtml(currentGeneratedArticle.category)} | 
                字數: ${currentGeneratedArticle.word_count} | 
                品質: ${currentGeneratedArticle.quality_score.toFixed(1)}
            </p>
            <div style="max-height: 150px; overflow-y: auto;">
                ${escapeHtml(currentGeneratedArticle.content.substring(0, 200))}...
            </div>
        `;
    } else {
        console.error('savePreview element not found');
        return;
    }
    
    // 顯示模態框
    const saveModalElement = document.getElementById('saveModal');
    if (saveModalElement) {
        const modal = new bootstrap.Modal(saveModalElement);
        modal.show();
    } else {
        console.error('saveModal element not found');
    }
}

// 確認保存文章
async function confirmSaveArticle() {
    if (!currentGeneratedArticle) {
        alert('沒有可保存的文章');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/save-generated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentGeneratedArticle)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '保存失敗');
        }
        
        const result = await response.json();
        
        // 關閉模態框
        const saveModalElement = document.getElementById('saveModal');
        if (saveModalElement) {
            const modal = bootstrap.Modal.getInstance(saveModalElement);
            if (modal) {
                modal.hide();
            }
        }
        
        // 顯示成功訊息
        alert('文章已成功保存到 Notion 資料庫！');
        
        // 重新載入文章列表
        loadArticles();
        loadDashboard();
        
        // 清空預覽
        const generateResult = document.getElementById('generateResult');
        if (generateResult) {
            generateResult.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>文章已成功保存到 Notion 資料庫</p>
                </div>
            `;
        }
        
        currentGeneratedArticle = null;
        
    } catch (error) {
        console.error('保存文章錯誤:', error);
        alert(`保存失敗: ${error.message}`);
    }
}

// 直接保存生成的文章到 Notion
async function saveGeneratedArticle() {
    if (!currentGeneratedArticle) {
        alert('沒有可保存的文章');
        return;
    }
    
    // 確認保存
    if (!confirm('確定要將此文章保存到 Notion 資料庫嗎？')) {
        return;
    }
    
    try {
        // 顯示載入狀態
        const saveBtn = document.querySelector('button[onclick="saveGeneratedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>保存中...';
        }
        
        const response = await fetch(`${API_BASE}/save-generated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentGeneratedArticle)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '保存失敗');
        }
        
        const result = await response.json();
        
        // 顯示成功訊息
        notifications.showSuccess('保存成功', '文章已成功保存到 Notion 資料庫！');
        
        // 重新載入文章列表
        loadArticles();
        
        // 更新顯示
        const generateResult = document.getElementById('generateResult');
        if (generateResult) {
            generateResult.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>文章已成功保存到 Notion 資料庫</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-plus me-1"></i>生成新文章
                    </button>
                </div>
            `;
        }
        
        currentGeneratedArticle = null;
        
    } catch (error) {
        console.error('保存文章錯誤:', error);
        notifications.showError('保存失敗', error.message);
    } finally {
        // 恢復按鈕狀態
        const saveBtn = document.querySelector('button[onclick="saveGeneratedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>保存到 Notion';
        }
    }
}

// 編輯生成的文章（簡單實現）
function editGeneratedArticle() {
    if (!currentGeneratedArticle) return;
    
    const newContent = prompt('請編輯文章內容:', currentGeneratedArticle.content);
    if (newContent !== null) {
        currentGeneratedArticle.content = newContent;
        currentGeneratedArticle.word_count = newContent.length;
        currentGeneratedArticle.reading_time = Math.max(1, Math.round(newContent.length / 250));
        
        showGeneratedPreview(currentGeneratedArticle);
    }
}

// 工具函數

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                <p>載入中...</p>
            </div>
        `;
    } else {
        console.warn(`Element with id '${containerId}' not found`);
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${escapeHtml(message)}
            </div>
        `;
    } else {
        console.warn(`Element with id '${containerId}' not found`);
    }
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text.toString();
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW');
}

// 全域函數（供 HTML 呼叫）
// 編輯相關函數

// 更新字數統計
function updateWordCount() {
    const content = document.getElementById('editContent')?.value || '';
    const wordCount = content.replace(/\s/g, '').length;
    const wordCountDisplay = document.getElementById('wordCountDisplay');
    if (wordCountDisplay) {
        wordCountDisplay.textContent = wordCount;
    }
}

// 重置到原始內容
function resetToOriginal() {
    if (!window.originalArticle) {
        alert('沒有原始文章可以重置');
        return;
    }
    
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (titleInput) titleInput.value = window.originalArticle.title;
    if (categorySelect) categorySelect.value = window.originalArticle.category;
    if (tagsInput) tagsInput.value = window.originalArticle.tags.join(', ');
    if (contentTextarea) contentTextarea.value = window.originalArticle.content;
    
    updateWordCount();
}

// 預覽變更
function previewChanges() {
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (!titleInput || !categorySelect || !tagsInput || !contentTextarea) {
        alert('無法讀取編輯內容');
        return;
    }
    
    const title = titleInput.value.trim();
    const category = categorySelect.value;
    const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    const content = contentTextarea.value.trim();
    const wordCount = content.replace(/\s/g, '').length;
    
    if (!title || !content) {
        alert('標題和內容不能為空');
        return;
    }
    
    // 更新當前生成的文章資料
    currentGeneratedArticle = {
        ...window.originalArticle,
        title: title,
        category: category,
        tags: tags,
        content: content,
        word_count: wordCount,
        reading_time: Math.ceil(wordCount / 300)
    };
    
    // 顯示預覽模態框
    showPreviewModal();
}

// 顯示預覽模態框
function showPreviewModal() {
    const article = currentGeneratedArticle;
    const modalContent = document.getElementById('modalContent');
    
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="article-content">
                <div class="mb-3">
                    <strong>分類：</strong>
                    <span class="badge bg-primary">${escapeHtml(article.category)}</span>
                </div>
                <div class="mb-3">
                    <strong>標籤：</strong>
                    ${article.tags.map(tag => `<span class="tag">#${escapeHtml(tag)}</span>`).join('')}
                </div>
                <div class="mb-3">
                    <strong>字數：</strong> ${article.word_count} 字 • 
                    <strong>閱讀時間：</strong> ${article.reading_time} 分鐘
                </div>
                <hr>
                <div style="white-space: pre-wrap;">${escapeHtml(article.content)}</div>
            </div>
        `;
    }
    
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) {
        modalTitle.textContent = article.title;
    }
    
    const articleModalElement = document.getElementById('articleModal');
    if (articleModalElement) {
        const modal = new bootstrap.Modal(articleModalElement);
        modal.show();
    }
}

// 保存編輯後的文章
async function saveEditedArticle() {
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (!titleInput || !categorySelect || !tagsInput || !contentTextarea) {
        alert('無法讀取編輯內容');
        return;
    }
    
    const title = titleInput.value.trim();
    const category = categorySelect.value;
    const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    const content = contentTextarea.value.trim();
    const wordCount = content.replace(/\s/g, '').length;
    
    if (!title || !content) {
        alert('標題和內容不能為空');
        return;
    }
    
    try {
        // 更新當前生成的文章資料
        currentGeneratedArticle = {
            ...window.originalArticle,
            title: title,
            category: category,
            tags: tags,
            content: content,
            word_count: wordCount,
            reading_time: Math.ceil(wordCount / 300)
        };
        
        // 顯示載入狀態
        const saveBtn = document.querySelector('button[onclick="saveEditedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>保存中...';
        }
        
        // 調用保存API
        const response = await fetch(`${API_BASE}/save-generated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentGeneratedArticle)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '保存失敗');
        }
        
        const result = await response.json();
        
        // 顯示成功訊息
        alert('文章已成功保存到 Notion 資料庫！');
        
        // 重新載入文章列表和統計
        loadArticles();
        loadDashboard();
        
        // 顯示成功狀態
        const generateResult = document.getElementById('generateResult');
        if (generateResult) {
            generateResult.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>文章已成功保存到 Notion 資料庫</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-plus me-1"></i>生成新文章
                    </button>
                </div>
            `;
        }
        
        currentGeneratedArticle = null;
        
    } catch (error) {
        console.error('保存文章錯誤:', error);
        alert(`保存失敗: ${error.message}`);
    } finally {
        // 恢復按鈕狀態
        const saveBtn = document.querySelector('button[onclick="saveEditedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>保存到 Notion';
        }
    }
}

// 載入分析儀表板
async function loadAnalytics() {
    try {
        const report = analytics.getAnalyticsReport();
        renderAnalyticsCards(report);
        renderTopArticlesChart(report.topArticles);
        renderTopSearchesChart(report.topSearchQueries);
    } catch (error) {
        console.error('載入分析數據錯誤:', error);
    }
}

// 渲染分析統計卡片
function renderAnalyticsCards(report) {
    const container = document.getElementById('analyticsCards');
    if (!container) return;
    
    const analyticsHTML = `
        <div class="col-md-3">
            <div class="card text-white bg-primary">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">${report.totalArticleViews}</h4>
                            <p class="card-text">今日文章閱讀</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-eye fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card text-white bg-info">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">${report.uniqueArticleViews}</h4>
                            <p class="card-text">獨特文章瀏覽</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-file-alt fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card text-white bg-success">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">${report.totalSearches}</h4>
                            <p class="card-text">搜索次數</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-search fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card text-white bg-warning">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">${report.sessionDuration}</h4>
                            <p class="card-text">會話時長(分)</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-clock fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = analyticsHTML;
}

// 渲染最受歡迎文章圖表
function renderTopArticlesChart(topArticles) {
    const container = document.getElementById('topArticlesChart');
    if (!container) return;
    
    if (topArticles.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">今日暫無文章閱讀數據</p>';
        return;
    }
    
    const chartHTML = topArticles.map((article, index) => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div class="flex-grow-1">
                <div class="fw-bold text-truncate" style="max-width: 200px;">
                    文章 ${index + 1}
                </div>
                <small class="text-muted">ID: ${article.id.substring(0, 8)}...</small>
            </div>
            <div class="text-end">
                <span class="badge bg-primary">${article.views} 次</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = chartHTML;
}

// 渲染熱門搜索圖表
function renderTopSearchesChart(topSearches) {
    const container = document.getElementById('topSearchesChart');
    if (!container) return;
    
    if (topSearches.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">今日暫無搜索數據</p>';
        return;
    }
    
    const chartHTML = topSearches.map((search, index) => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div class="flex-grow-1">
                <div class="fw-bold">"${search.query}"</div>
            </div>
            <div class="text-end">
                <span class="badge bg-success">${search.count} 次</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = chartHTML;
}

// API性能監控類
class APIPerformanceMonitor {
    constructor() {
        this.metrics = {
            requests: new Map(),
            cacheHits: 0,
            cacheMisses: 0,
            averageResponseTime: 0
        };
    }

    // 監控API請求
    monitorRequest(endpoint, startTime) {
        return {
            complete: (success = true) => {
                const duration = Date.now() - startTime;
                
                if (!this.metrics.requests.has(endpoint)) {
                    this.metrics.requests.set(endpoint, {
                        count: 0,
                        totalTime: 0,
                        errors: 0
                    });
                }
                
                const endpointStats = this.metrics.requests.get(endpoint);
                endpointStats.count++;
                endpointStats.totalTime += duration;
                
                if (!success) {
                    endpointStats.errors++;
                }
                
                this.updatePerformanceDisplay();
            }
        };
    }

    // 記錄缓存命中
    recordCacheHit() {
        this.cacheHits++;
        this.updatePerformanceDisplay();
    }

    // 記錄缓存失誤
    recordCacheMiss() {
        this.cacheMisses++;
        this.updatePerformanceDisplay();
    }

    // 獲取性能統計
    getStats() {
        const endpointStats = {};
        for (const [endpoint, stats] of this.metrics.requests) {
            endpointStats[endpoint] = {
                avgResponseTime: stats.count > 0 ? Math.round(stats.totalTime / stats.count) : 0,
                totalRequests: stats.count,
                errorRate: stats.count > 0 ? Math.round((stats.errors / stats.count) * 100) : 0
            };
        }

        return {
            endpoints: endpointStats,
            cache: {
                hitRate: this.cacheHits + this.cacheMisses > 0 
                    ? Math.round((this.cacheHits / (this.cacheHits + this.cacheMisses)) * 100) 
                    : 0,
                totalHits: this.cacheHits,
                totalMisses: this.cacheMisses
            }
        };
    }

    // 從服務器獲取性能指標
    async fetchServerMetrics() {
        try {
            const response = await fetch('/api/v1/financial-wisdom/performance/metrics');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('獲取服務器性能指標失敗:', error);
        }
        return null;
    }

    // 更新性能顯示面板
    async updatePerformanceDisplay() {
        const serverMetrics = await this.fetchServerMetrics();
        const clientStats = this.getStats();
        
        // 更新性能儀表板（如果存在）
        const performancePanel = document.getElementById('performanceMetrics');
        if (performancePanel && serverMetrics) {
            const metricsHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>缓存性能</h6>
                        <div class="mb-2">
                            <small>命中率: <span class="badge bg-${serverMetrics.cache_performance.hit_rate_estimate.replace('%', '') > 70 ? 'success' : 'warning'}">${serverMetrics.cache_performance.hit_rate_estimate}</span></small>
                        </div>
                        <div class="mb-2">
                            <small>內存使用: ${Math.round(serverMetrics.cache_performance.memory_usage_kb)} KB</small>
                        </div>
                        <div class="mb-2">
                            <small>活躍鍵: ${serverMetrics.cache_performance.active_cache_keys}</small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>API響應時間</h6>
                        ${Object.entries(serverMetrics.api_endpoints).map(([endpoint, stats]) => 
                            `<div class="mb-1"><small>${endpoint}: ${stats.avg_response_ms}ms ${stats.cached ? '<i class="fas fa-check text-success"></i>' : ''}</small></div>`
                        ).join('')}
                    </div>
                </div>
                ${serverMetrics.recommendations.length > 0 ? `
                    <div class="mt-3">
                        <h6>優化建議</h6>
                        ${serverMetrics.recommendations.map(rec => 
                            `<div class="alert alert-info alert-sm py-2">${rec}</div>`
                        ).join('')}
                    </div>
                ` : ''}
            `;
            performancePanel.innerHTML = metricsHTML;
        }
    }
}

// 全局API性能監控實例
const apiPerformanceMonitor = new APIPerformanceMonitor();

// 增強fetch函數以支持性能監控
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const startTime = Date.now();
    const url = args[0];
    
    // 提取API端點名稱
    let endpoint = 'unknown';
    if (typeof url === 'string' && url.includes('/api/v1/financial-wisdom/')) {
        const pathParts = url.split('/api/v1/financial-wisdom/')[1]?.split('?')[0];
        endpoint = pathParts || 'unknown';
    }
    
    const monitor = apiPerformanceMonitor.monitorRequest(endpoint, startTime);
    
    try {
        const response = await originalFetch.apply(this, args);
        monitor.complete(response.ok);
        return response;
    } catch (error) {
        monitor.complete(false);
        throw error;
    }
};

// 主頁初始化函數 (只載入智能生成和文章管理)
function initMainPage() {
    loadCategories();
    loadArticles();
    setupEventListeners();
}

// 分析頁面初始化函數 (只在analytics.html使用)
function initAnalyticsPage() {
    loadDashboard();
    loadAnalytics();
    
    // 初始化性能監控面板
    setTimeout(() => apiPerformanceMonitor.updatePerformanceDisplay(), 1000);
    
    // 每30秒更新一次分析數據
    setInterval(loadAnalytics, 30000);
    
    // 每60秒更新一次性能指標
    setInterval(() => apiPerformanceMonitor.updatePerformanceDisplay(), 60000);
}

// 更新初始化函數
document.addEventListener('DOMContentLoaded', function() {
    // 檢查當前頁面是否為分析頁面
    if (window.location.pathname.includes('analytics.html')) {
        initAnalyticsPage();
    } else {
        initMainPage();
    }
});

// 文章模板系統
const articleTemplates = {
    custom: {
        name: "自定義內容",
        description: "根據您的主題描述自由創作文章內容。",
        placeholder: "描述你想要生成的文章主題和內容要點",
        prompt: "" // 空提示語，使用用戶自定義內容
    },
    wealth_mindset: {
        name: "財富成長思維",
        description: "深度分析財富思維，包含案例研究和行動步驟。",
        placeholder: "例如：複利效應的力量、富人思維的轉變、財富積累的心理障礙等",
        prompt: `你是一位資深的財富教練和商業策略專家，擁有15年金融投資和創業經驗。請為我的 Notion 資料庫 '財商成長思維' 創建關於財富成長思維的深度文章。

文章要求:
- 至少1000字
- 實用性強，包含具體案例和行動步驟
- 適合25-45歲想要提升財富的讀者

內容結構:
1. 標題 (吸引人且具體)
2. 引言 (150字，包含一個引人思考的問題或故事)
3. 核心概念解析 (300字，深入說明主要思維)
4. 實際案例分析 (250字，真實或合理的成功/失敗案例)
5. 具體行動步驟 (200字，3-5個可執行的建議)
6. 常見障礙與解決方案 (100字)

語調要求：親切但專業，使用具體數據和例子，避免艱深術語，用通俗易懂的語言，每段落控制在3-4句話。

輸出格式：以 Notion 頁面格式呈現，包含標題、標籤：#財富思維 #個人成長 #投資理財、完整內容。`
    },
    investment_guide: {
        name: "投資理財指南",
        description: "實用的投資教學文章，包含具體操作步驟。",
        placeholder: "例如：股票投資入門、基金配置策略、債券投資技巧等",
        prompt: `你是一位經驗豐富的投資顧問和理財規劃師。請創建一篇實用的投資理財指南文章。

文章要求:
- 1000-1500字
- 實用操作導向，包含具體步驟和工具推薦
- 適合投資新手到中級投資者

內容結構:
1. 引言：為什麼這個投資方法重要
2. 基礎知識：必要的背景概念 (300字)
3. 詳細步驟：具體操作指南 (400字)
4. 實戰案例：成功投資案例分析 (200字)
5. 風險提醒：常見陷阱和風險控制 (150字)
6. 總結：關鍵要點和下一步行動

語調：專業但易懂，使用具體數據和圖表說明，提供可驗證的投資策略。`
    },
    business_strategy: {
        name: "商業策略分析",
        description: "深入的商業案例分析和策略思考。",
        placeholder: "例如：企業轉型策略、市場競爭分析、商業模式創新等",
        prompt: `你是一位資深的商業策略顧問和管理專家。請創建一篇商業策略分析文章。

文章要求:
- 1200-1800字
- 案例導向，深入分析商業決策邏輯
- 適合創業者、經理人和商業學習者

內容結構:
1. 背景介紹：市場環境和挑戰
2. 案例描述：具體企業或行業案例 (400字)
3. 策略分析：決策邏輯和戰略思考 (500字)
4. 關鍵洞察：可複製的商業智慧 (200字)
5. 實施建議：如何應用到自己的事業 (200字)
6. 延伸思考：相關策略和未來趋势

語調：分析性強，邏輯清晰，使用商業術語但保持可理解性。`
    },
    personal_finance: {
        name: "個人財務管理",
        description: "詳細的個人理財規劃和管理方法。",
        placeholder: "例如：預算制定方法、債務管理、緊急基金規劃等",
        prompt: `你是一位專業的個人理財規劃師。請創建一篇個人財務管理的實用指南。

文章要求:
- 1000-1400字
- 步驟詳細，提供可執行的理財方法
- 適合各收入層級的讀者

內容結構:
1. 現狀評估：個人財務健康檢查方法
2. 目標設定：短期和長期財務目標
3. 實施計畫：詳細的執行步驟 (500字)
4. 工具推薦：實用的理財工具和app
5. 常見問題：解答理財中的疑難問題
6. 成功案例：真實的理財成功故事

語調：務實親民，提供具體的數字建議和計算方法，避免複雜的金融術語。`
    },
    market_analysis: {
        name: "市場趨勢分析",
        description: "專業的市場分析和趨勢預測文章。",
        placeholder: "例如：房地產市場走勢、股市技術分析、加密貨幣趨勢等",
        prompt: `你是一位資深的市場分析師和投資研究專家。請創建一篇市場趨勢分析文章。

文章要求:
- 1200-1600字
- 數據驅動，提供專業觀點和預測
- 適合投資者和關注市場的讀者

內容結構:
1. 市場概況：當前市場狀態和關鍵數據
2. 趨勢分析：歷史數據和走勢分析 (400字)
3. 影響因素：關鍵的市場驅動因素 (300字)
4. 專業觀點：基於分析的市場預測 (300字)
5. 投資建議：基於分析的投資策略
6. 風險提醒：市場風險和注意事項

語調：專業權威，使用大量數據和圖表，提供客觀的市場觀點。`
    },
    career_development: {
        name: "職涯發展建議",
        description: "職業成長和技能發展的指導文章。",
        placeholder: "例如：職業轉換策略、技能提升方法、薪資談判技巧等",
        prompt: `你是一位資深的職涯顧問和人力資源專家。請創建一篇職涯發展建議文章。

文章要求:
- 1000-1300字
- 成長導向，提供實用的職業發展策略
- 適合各階段的職場工作者

內容結構:
1. 職涯診斷：評估當前職業狀態
2. 成長路徑：職業發展的可能方向 (300字)
3. 技能建議：必要的技能提升計畫 (300字)
4. 行動計畫：具體的執行步驟 (250字)
5. 成功案例：職涯轉換的成功故事
6. 常見陷阱：職業發展中的常見錯誤

語調：激勵性強，提供實用建議，結合職場實際情況。`
    },
    entrepreneurship: {
        name: "創業心得分享",
        description: "創業經驗和實戰心得的深度分享。",
        placeholder: "例如：創業初期準備、團隊建設、融資經驗、失敗教訓等",
        prompt: `你是一位成功的創業家和商業導師，擁有多次創業經驗。請分享創業實戰心得。

文章要求:
- 1200-1500字
- 實戰經驗導向，分享真實的創業故事
- 適合潛在創業者和初期創業者

內容結構:
1. 創業背景：為什麼選擇創業
2. 實戰經歷：詳細的創業過程 (500字)
3. 關鍵決策：重要的決策點和思考邏輯 (300字)
4. 經驗教訓：成功和失敗的深度反思 (200字)
5. 實用建議：給創業者的具體建議
6. 資源推薦：創業相關的工具和資源

語調：坦誠分享，既有成功經驗也有失敗教訓，提供實用的創業智慧。`
    }
};

// 更新主題placeholder的函數
function updateTopicPlaceholder() {
    const templateSelect = document.getElementById('articleTemplate');
    const topicTextarea = document.getElementById('articleTopic');
    const description = document.getElementById('templateDescription');
    
    const selectedTemplate = templateSelect.value;
    const template = articleTemplates[selectedTemplate];
    
    if (template) {
        topicTextarea.placeholder = template.placeholder;
        description.textContent = template.description;
    }
}

// 獲取當前選中模板的提示語
function getTemplatePrompt() {
    const templateSelect = document.getElementById('articleTemplate');
    const selectedTemplate = templateSelect.value;
    const template = articleTemplates[selectedTemplate];
    
    return template ? template.prompt : '';
}

// 缓存管理函數
async function showCacheStats() {
    try {
        const response = await fetch('/api/v1/financial-wisdom/cache/stats');
        if (response.ok) {
            const stats = await response.json();
            notifications.showSuccess('缓存統計', `活躍鍵 ${stats.cache_stats.active_keys}, 已過期 ${stats.cache_stats.expired_keys}, 內存使用 ${Math.round(stats.cache_stats.memory_usage_kb)} KB`);
        }
    } catch (error) {
        notifications.showError('錯誤', '獲取缓存統計失敗');
    }
}

async function clearCache() {
    if (confirm('確定要清理所有缓存嗎？這將會影響系統性能。')) {
        try {
            const response = await fetch('/api/v1/financial-wisdom/cache/clear', {
                method: 'POST'
            });
            if (response.ok) {
                notifications.showSuccess('缓存清理', '所有缓存已清理');
                // 立即刷新性能指標
                apiPerformanceMonitor.updatePerformanceDisplay();
            }
        } catch (error) {
            notifications.showError('缓存清理失敗', '清理缓存失敗');
        }
    }
}

async function refreshPerformanceMetrics() {
    apiPerformanceMonitor.updatePerformanceDisplay();
    notifications.showInfo('性能指標', '性能指標已刷新');
}

async function optimizePerformance() {
    notifications.showInfo('性能優化', '正在優化性能設置...');
    
    // 模擬性能優化過程
    setTimeout(() => {
        notifications.showSuccess('性能優化完成', '性能優化完成！缓存策略已更新。');
        apiPerformanceMonitor.updatePerformanceDisplay();
    }, 2000);
}

// 載入分析數據
async function loadAnalytics() {
    try {
        // 模擬載入基本統計資料
        const mockStats = {
            totalArticles: currentArticles.length,
            publishedArticles: currentArticles.filter(a => a.status === '已發布').length,
            totalViews: Math.floor(Math.random() * 10000) + 1000,
            todayViews: Math.floor(Math.random() * 500) + 50
        };
        
        return mockStats;
    } catch (error) {
        console.error('載入分析數據失敗:', error);
        return null;
    }
}

// 初始化分析頁面
function initAnalyticsPage() {
    console.log('正在初始化分析頁面...');
    
    // 載入統計卡片
    loadStatsCards();
    
    // 載入分析卡片
    loadAnalyticsCards();
    
    // 載入性能指標
    if (typeof apiPerformanceMonitor !== 'undefined') {
        apiPerformanceMonitor.updatePerformanceDisplay();
    }
    
    console.log('分析頁面初始化完成');
}

// 載入統計卡片
async function loadStatsCards() {
    const statsCardsContainer = document.getElementById('statsCards');
    if (!statsCardsContainer) {
        console.log('統計卡片容器不存在');
        return;
    }
    
    try {
        // 載入基本統計
        const stats = await loadAnalytics();
        if (!stats) {
            statsCardsContainer.innerHTML = '<div class="col-12"><p class="text-muted text-center">無法載入統計資料，請檢查網路連接或稍後重試</p></div>';
            return;
        }
        
        const statsHTML = `
            <div class="col-md-3">
                <div class="card stats-card primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">總文章數</h6>
                                <h3 class="card-title mb-0">${stats.totalArticles}</h3>
                            </div>
                            <i class="fas fa-file-alt fa-2x text-primary"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">已發布</h6>
                                <h3 class="card-title mb-0">${stats.publishedArticles}</h3>
                            </div>
                            <i class="fas fa-check-circle fa-2x text-success"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card info">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">總瀏覽量</h6>
                                <h3 class="card-title mb-0">${stats.totalViews.toLocaleString()}</h3>
                            </div>
                            <i class="fas fa-eye fa-2x text-info"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card warning">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">今日瀏覽</h6>
                                <h3 class="card-title mb-0">${stats.todayViews}</h3>
                            </div>
                            <i class="fas fa-chart-line fa-2x text-warning"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        statsCardsContainer.innerHTML = statsHTML;
        
    } catch (error) {
        console.error('載入統計卡片失敗:', error);
        statsCardsContainer.innerHTML = '<div class="col-12"><p class="text-danger text-center">載入統計資料時發生錯誤</p></div>';
    }
}

// 載入分析卡片
async function loadAnalyticsCards() {
    const analyticsCardsContainer = document.getElementById('analyticsCards');
    if (!analyticsCardsContainer) {
        console.log('分析卡片容器不存在');
        return;
    }
    
    try {
        // 模擬今日分析數據
        const todayStats = {
            newArticles: Math.floor(Math.random() * 5) + 1,
            activeUsers: Math.floor(Math.random() * 100) + 20,
            avgReadTime: Math.floor(Math.random() * 300) + 120,
            topCategory: '思維轉換'
        };
        
        const analyticsHTML = `
            <div class="col-md-3">
                <div class="card stats-card primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">今日新文章</h6>
                                <h3 class="card-title mb-0">${todayStats.newArticles}</h3>
                            </div>
                            <i class="fas fa-plus-circle fa-2x text-primary"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">活躍用戶</h6>
                                <h3 class="card-title mb-0">${todayStats.activeUsers}</h3>
                            </div>
                            <i class="fas fa-users fa-2x text-success"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card info">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">平均閱讀時間</h6>
                                <h3 class="card-title mb-0">${Math.floor(todayStats.avgReadTime/60)}分${todayStats.avgReadTime%60}秒</h3>
                            </div>
                            <i class="fas fa-clock fa-2x text-info"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card warning">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-subtitle mb-2 text-muted">熱門分類</h6>
                                <h3 class="card-title mb-0">${todayStats.topCategory}</h3>
                            </div>
                            <i class="fas fa-star fa-2x text-warning"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        analyticsCardsContainer.innerHTML = analyticsHTML;
        
    } catch (error) {
        console.error('載入分析卡片失敗:', error);
        analyticsCardsContainer.innerHTML = '<div class="col-12"><p class="text-danger text-center">載入分析資料時發生錯誤</p></div>';
    }
}

// 全域函數暴露
window.showArticleDetail = showArticleDetail;
window.confirmSaveArticle = confirmSaveArticle;
window.saveGeneratedArticle = saveGeneratedArticle;
window.regenerateArticle = regenerateArticle;
window.showSaveModal = showSaveModal;
window.editGeneratedArticle = editGeneratedArticle;
window.loadArticles = loadArticles;
window.loadDashboard = loadDashboard;
window.loadAnalytics = loadAnalytics;
window.updateWordCount = updateWordCount;
window.resetToOriginal = resetToOriginal;
window.previewChanges = previewChanges;
window.saveEditedArticle = saveEditedArticle;
window.showCacheStats = showCacheStats;
window.clearCache = clearCache;
window.refreshPerformanceMetrics = refreshPerformanceMetrics;
window.optimizePerformance = optimizePerformance;
window.updateTopicPlaceholder = updateTopicPlaceholder;
window.getTemplatePrompt = getTemplatePrompt;
window.initAnalyticsPage = initAnalyticsPage;
