document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:5001/api';

    // --- 通用函数 ---
    function generateContractList(productCode) {
        if (!productCode) return [];
        const contracts = [];
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const yearSuffix = currentYear.toString().slice(-2);
        const nextYearSuffix = (currentYear + 1).toString().slice(-2);

        for (let month = currentMonth; month <= 12; month++) {
            contracts.push(`${productCode}${yearSuffix}${String(month).padStart(2, '0')}`);
        }
        for (let month = 1; month < currentMonth; month++) {
            contracts.push(`${productCode}${nextYearSuffix}${String(month).padStart(2, '0')}`);
        }
        return contracts;
    }

    function populateContractSelect(productCode, selectElement) {
        const contracts = generateContractList(productCode);
        selectElement.innerHTML = '';
        if (contracts.length > 0) {
            contracts.forEach(contract => {
                const option = document.createElement('option');
                option.value = contract;
                option.textContent = contract;
                selectElement.appendChild(option);
            });
        } else {
            selectElement.innerHTML = '<option value="">无可用合约</option>';
        }
    }

    // --- 实时策略模块 ---
    const strategyForm = document.getElementById('strategy-form');
    const strategyResult = document.getElementById('strategy-result');
    const strategyInstrumentSelect = document.getElementById('strategy-instrument');
    const strategyContractSelect = document.getElementById('strategy-contract');
    const strategyPeriodSelect = document.getElementById('strategy-period');

    strategyInstrumentSelect.addEventListener('change', (e) => {
        populateContractSelect(e.target.value, strategyContractSelect);
    });
    populateContractSelect(strategyInstrumentSelect.value, strategyContractSelect);

    strategyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const contract = strategyContractSelect.value;
        const period = strategyPeriodSelect.value;

        if (!contract) {
            strategyResult.innerHTML = `<p style="color: red;">请选择一个具体的合约。</p>`;
            return;
        }

        const data = { instrument: contract, period: period };
        strategyResult.innerHTML = '<p>正在执行策略...</p>';

        try {
            const response = await fetch(`${API_BASE_URL}/strategy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `HTTP 错误! 状态: ${response.status}`);

            strategyResult.innerHTML = `
                <p><strong>合约:</strong> ${result.instrument}</p>
                <p><strong>周期:</strong> ${result.period}</p>
                <p><strong>操作:</strong> <span style="color: ${getActionColor(result.action)};">${result.action}</span></p>
                <p><strong>价格:</strong> ${result.price}</p>
                <p><strong>时间:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
            `;
        } catch (error) {
            strategyResult.innerHTML = `<p style="color: red;">执行失败: ${error.message}</p>`;
        }
    });

    // --- 策略回测模块 ---
    const backtestForm = document.getElementById('backtest-form');
    const backtestResult = document.getElementById('backtest-result');
    const backtestInstrumentSelect = document.getElementById('backtest-instrument');
    const backtestContractSelect = document.getElementById('backtest-contract');
    const backtestPeriodSelect = document.getElementById('backtest-period');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const initialCapitalInput = document.getElementById('initial-capital');

    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    const oneYearAgo = new Date(today);
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    startDateInput.value = oneYearAgo.toISOString().split('T')[0];
    endDateInput.value = yesterday.toISOString().split('T')[0];

    backtestInstrumentSelect.addEventListener('change', (e) => {
        populateContractSelect(e.target.value, backtestContractSelect);
    });
    populateContractSelect(backtestInstrumentSelect.value, backtestContractSelect);

    backtestForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const contract = backtestContractSelect.value;
        if (!contract) {
            backtestResult.innerHTML = `<p style="color: red;">请选择一个具体的合约。</p>`;
            return;
        }

        const data = {
            instrument: contract,
            period: backtestPeriodSelect.value,
            start_date: startDateInput.value,
            end_date: endDateInput.value,
            initial_capital: parseFloat(initialCapitalInput.value)
        };

        backtestResult.innerHTML = '<p>正在进行回测...</p>';

        try {
            const response = await fetch(`${API_BASE_URL}/backtest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `HTTP 错误! 状态: ${response.status}`);
            
            let tradesHtml = '<ul>';
            if (result.trades && result.trades.length > 0) {
                result.trades.forEach(trade => tradesHtml += `<li>${trade}</li>`);
            } else {
                tradesHtml += '<li>无交易记录</li>';
            }
            tradesHtml += '</ul>';

            backtestResult.innerHTML = `
                <p><strong>合约:</strong> ${result.instrument}</p>
                <p><strong>时间范围:</strong> ${result.time_range}</p>
                <p><strong>初始资金:</strong> ${result.initial_capital.toLocaleString()}</p>
                <p><strong>最终资金:</strong> ${result.final_capital.toLocaleString()}</p>
                <p><strong>总回报率:</strong> <span style="color: ${result.total_return_pct >= 0 ? 'green' : 'red'};">${result.total_return_pct}%</span></p>
                <p><strong>夏普比率:</strong> ${result.sharpe_ratio}</p>
                <p><strong>总交易次数:</strong> ${result.trade_count}</p>
                <p><strong>最近 ${result.trades.length} 笔交易:</strong></p>
                ${tradesHtml}
            `;
        } catch (error) {
            backtestResult.innerHTML = `<p style="color: red;">回测失败: ${error.message}</p>`;
        }
    });

    function getActionColor(action) {
        switch (action) {
            case '多开': return 'green';
            case '空开': return 'red';
            case '平仓': return 'orange';
            default: return 'gray';
        }
    }
});
