import { ITEM_NAMES_MAP } from './constants.js';

export const getRealName = (id) => ITEM_NAMES_MAP[id] || id;

export const levelToFame = (lvl) => {
    if (lvl <= 1) return 0;
    return 30000000 * Math.pow((lvl - 1) / 99, 2.5);
};

export const fameToLevel = (fame) => {
    if (fame <= 0) return 1;
    return Math.min(100, Math.floor(1 + 99 * Math.pow(fame / 30000000, 0.4)));
};

export const formatK = (num) => {
    if (!num || num === 0) return '0';
    const abs = Math.abs(num);
    if (abs >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    return abs >= 1000 ? (num / 1000).toFixed(1) + 'k' : num.toString();
};

export const getStackInfo = (qty) => {
    if (!qty) return "0 Pcs";
    const cQty = Math.ceil(Number(qty));
    const stacks = Math.floor(cQty / 999);
    const rem = Math.floor(cQty % 999);
    return stacks > 0 ? `${cQty.toLocaleString('en-US')} Pcs (${stacks} Stk + ${rem})` : `${cQty.toLocaleString('en-US')} Pcs`;
};

export const getBMBaseVolume = (cat, tier, enchant) => {
    const isWeapon = cat.includes('weapons'); 
    const t = parseInt(tier);
    
    if (isWeapon) {
        if (enchant === '.0') return t === 4 ? 6 : t === 5 ? 4 : t === 6 ? 3 : t === 7 ? 2 : 1;
        if (enchant === '.1') return t === 4 ? 2 : 1;
        return 1;
    } else {
        if (enchant === '.0') return t === 4 ? 27 : t === 5 ? 16 : t === 6 ? 8 : t === 7 ? 4 : 2;
        if (enchant === '.1') return t === 4 ? 8 : t === 5 ? 5 : t === 6 ? 2 : 1;
        if (enchant === '.2') return t === 4 ? 2 : 1;
        return 1;
    }
};