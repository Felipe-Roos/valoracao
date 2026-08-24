(function () {
    'use strict';

    var config = window.VALUATION_CONFIG;
    var list = document.getElementById('confirmed-entries');
    var totalEl = document.getElementById('running-total');

    function formatBRL(value) {
        return Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function computeRow(row) {
        var quantity = parseFloat(row.querySelector('.field-quantity').value) || 1;
        var baseValue = parseFloat(row.querySelector('.field-base-value').value) || 0;

        var multiplierProduct = 1;
        var additive = 0;
        var applied = [];

        row.querySelectorAll('.multiplier-input').forEach(function (input) {
            if (!input.checked) return;

            var type = input.dataset.type;
            var factor = input.dataset.factor !== '' ? parseFloat(input.dataset.factor) : null;
            var multiplierId = input.dataset.multiplierId;
            var label = input.closest('label').textContent.trim();

            if (type === 'multiply') {
                multiplierProduct *= factor;
                applied.push({ id: multiplierId, label: label, factor_type: type, factor_value: factor });
            } else if (type === 'variable_multiply') {
                var varInput = row.querySelector('.multiplier-variable-input[data-multiplier-id="' + multiplierId + '"]');
                var varValue = parseFloat(varInput.value) || 1;
                multiplierProduct *= varValue;
                applied.push({ id: multiplierId, label: label, factor_type: type, variable_input: varValue });
            } else if (type === 'add_per_unit') {
                var unitInput = row.querySelector('.multiplier-unit-input[data-multiplier-id="' + multiplierId + '"]');
                var n = parseFloat(unitInput.value) || 0;
                additive += n * factor;
                applied.push({ id: multiplierId, label: label, factor_type: type, unit_quantity: n, factor_value: factor });
            }
        });

        var totalMultiplier = multiplierProduct + additive;
        var value = baseValue * quantity * totalMultiplier;

        return { value: value, quantity: quantity, baseValue: baseValue, applied: applied };
    }

    function updateRowPreview(row) {
        var result = computeRow(row);
        row.querySelector('.preview-value').textContent = 'R$ ' + formatBRL(result.value);
    }

    function resetRow(row) {
        row.querySelector('.product-check').checked = false;
        row.querySelector('.product-detail').hidden = true;
        row.querySelector('.field-quantity').value = 1;
        row.querySelector('.field-notes').value = '';
        row.querySelector('.field-final-value').value = '';
        row.querySelectorAll('.multiplier-input').forEach(function (input) { input.checked = false; });
        row.querySelectorAll('.multiplier-variable-input, .multiplier-unit-input').forEach(function (input) {
            input.value = '';
            input.disabled = true;
        });
        updateRowPreview(row);
    }

    function appendEntry(data) {
        var li = document.createElement('li');
        li.dataset.entryId = data.id;

        var productSpan = document.createElement('span');
        productSpan.className = 'entry-product';
        productSpan.textContent = data.product_name;

        var valueSpan = document.createElement('span');
        valueSpan.className = 'entry-value';
        valueSpan.textContent = 'R$ ' + formatBRL(data.final_value);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'remove-entry-btn';
        removeBtn.dataset.entryId = data.id;
        removeBtn.textContent = 'remover';

        li.appendChild(productSpan);
        li.appendChild(valueSpan);
        li.appendChild(removeBtn);

        var emptyItem = list.querySelector('.empty-item');
        if (emptyItem) emptyItem.remove();

        list.prepend(li);
    }

    function confirmEntry(row) {
        var statusEl = row.querySelector('.save-status');
        var finalValueInput = row.querySelector('.field-final-value');
        var finalValue = parseFloat(finalValueInput.value);

        if (Number.isNaN(finalValue)) {
            statusEl.textContent = 'Informe o valor final antes de confirmar.';
            statusEl.className = 'save-status error';
            return;
        }

        var result = computeRow(row);
        var payload = {
            product_id: row.dataset.productId,
            quantity: result.quantity,
            base_value: result.baseValue,
            final_value: finalValue,
            notes: row.querySelector('.field-notes').value,
            applied_multipliers: result.applied
        };

        statusEl.textContent = 'Salvando...';
        statusEl.className = 'save-status';

        fetch(config.entryCreateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': config.csrfToken
            },
            body: JSON.stringify(payload)
        })
            .then(function (response) {
                if (!response.ok) throw new Error('Falha ao salvar.');
                return response.json();
            })
            .then(function (data) {
                appendEntry(data);
                totalEl.textContent = formatBRL(data.total);
                resetRow(row);
            })
            .catch(function () {
                statusEl.textContent = 'Erro ao salvar. Tente novamente.';
                statusEl.className = 'save-status error';
            });
    }

    document.querySelectorAll('.product-row').forEach(function (row) {
        var checkbox = row.querySelector('.product-check');
        var detail = row.querySelector('.product-detail');

        checkbox.addEventListener('change', function () {
            detail.hidden = !checkbox.checked;
            if (checkbox.checked) updateRowPreview(row);
        });

        row.querySelectorAll('.multiplier-input').forEach(function (input) {
            input.addEventListener('change', function () {
                var id = input.dataset.multiplierId;
                var varInput = row.querySelector('.multiplier-variable-input[data-multiplier-id="' + id + '"]');
                var unitInput = row.querySelector('.multiplier-unit-input[data-multiplier-id="' + id + '"]');
                if (varInput) varInput.disabled = !input.checked;
                if (unitInput) unitInput.disabled = !input.checked;
                updateRowPreview(row);
            });
        });

        row.querySelectorAll('.multiplier-variable-input, .multiplier-unit-input, .field-quantity, .field-base-value')
            .forEach(function (input) {
                input.addEventListener('input', function () { updateRowPreview(row); });
            });

        row.querySelector('.use-suggestion-btn').addEventListener('click', function () {
            var result = computeRow(row);
            row.querySelector('.field-final-value').value = result.value.toFixed(2);
        });

        row.querySelector('.confirm-btn').addEventListener('click', function () {
            confirmEntry(row);
        });
    });

    list.addEventListener('click', function (event) {
        if (!event.target.classList.contains('remove-entry-btn')) return;
        var entryId = event.target.dataset.entryId;
        var url = config.entryDeleteUrlTemplate.replace('__ID__', entryId);

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': config.csrfToken }
        })
            .then(function (response) {
                if (!response.ok) throw new Error('Falha ao remover.');
                return response.json();
            })
            .then(function (data) {
                event.target.closest('li').remove();
                totalEl.textContent = formatBRL(data.total);
                if (!list.querySelector('li')) {
                    var emptyItem = document.createElement('li');
                    emptyItem.className = 'empty-item';
                    emptyItem.textContent = 'Nenhum item confirmado ainda.';
                    list.appendChild(emptyItem);
                }
            });
    });
})();
