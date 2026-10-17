import { parseMtopJsonp } from './mtop.js';
export const SEARCH_MTOP_API = 'mtop.relationrecommend.wirelessrecommend.recommend';
export const SEARCH_APP_ID = '32517';
function bool(s) {
    return s === 'true' || s === true;
}
function parseCountText(text) {
    if (typeof text === 'number')
        return Number.isFinite(text) ? text : null;
    if (!text)
        return null;
    const compact = String(text).replace(/,/g, '').replace(/\s+/g, '');
    const match = compact.match(/(\d+(?:\.\d+)?)(万|w|W|亿|k|K)?/);
    if (!match?.[1])
        return null;
    const value = Number(match[1]);
    if (!Number.isFinite(value))
        return null;
    const unit = match[2] ?? '';
    const multiplier = unit === '亿'
        ? 100000000
        : unit === '万' || unit === 'w' || unit === 'W'
            ? 10000
            : unit === 'k' || unit === 'K'
                ? 1000
                : 1;
    return Math.round(value * multiplier);
}
function parsePercentText(text) {
    if (!text)
        return null;
    const match = String(text).match(/(\d+(?:\.\d+)?)\s*%/);
    if (!match?.[1])
        return null;
    const n = Number(match[1]);
    return Number.isFinite(n) ? n : null;
}
function textList(items) {
    return (items ?? [])
        .map((t) => t?.text?.trim() ?? '')
        .filter((s) => !!s);
}
function parseUrlParam(rawUrl, key) {
    if (!rawUrl)
        return null;
    try {
        const u = new URL(rawUrl, 'https://www.1688.com');
        return u.searchParams.get(key);
    }
    catch {
        return null;
    }
}
export function extractTrendSignals(d) {
    const rawGuides = [
        ...(Array.isArray(d?.list?.guide) ? d.list.guide : []),
        ...(Array.isArray(d?.list?.guide2) ? d.list.guide2 : []),
        ...(Array.isArray(d?.grid?.guide) ? d.grid.guide : []),
        ...(Array.isArray(d?.grid?.guide2) ? d.grid.guide2 : []),
    ];
    const seenGuideKeys = new Set();
    const newProductSellPoints = [];
    const rankBadges = [];
    const businessOppoTopics = [];
    const priceCompetitiveBadges = [];
    for (const g of rawGuides) {
        if (!g || typeof g !== 'object')
            continue;
        const matKey = String(g.matKey ?? '').trim();
        const text = String(g.text ?? '').trim();
        const url = String(g.url ?? '').trim();
        if (!text)
            continue;
        const dedupKey = `${matKey}::${text}`;
        if (seenGuideKeys.has(dedupKey))
            continue;
        seenGuideKeys.add(dedupKey);
        if (matKey === 'newProductSellPoint' || /^(功能|材质|设计|款式|工艺)上新|新品/.test(text)) {
            newProductSellPoints.push(text);
        }
        else if (matKey === 'billboard' && (url.includes('newRank') || /榜第\d+名/.test(text))) {
            const rankMatch = text.match(/^(.*?榜)第(\d+)名/);
            rankBadges.push({
                text,
                rankName: parseUrlParam(url, 'rankName') ?? (rankMatch ? rankMatch[1] : text),
                rankNumber: rankMatch ? parseInt(rankMatch[2], 10) : null,
                categoryId: parseUrlParam(url, 'categoryId'),
                rankFullNameId: parseUrlParam(url, 'rankFullNameId'),
                url: url || null,
            });
        }
        else if (matKey === 'billboard' && (url.includes('business-oppo') || text.startsWith('商机组货'))) {
            const topic = text.replace(/^商机组货[：:]\s*/, '').trim();
            const topicId = parseUrlParam(url, 'topicId');
            const dateMatch = topicId ? topicId.match(/^(20\d{2})(\d{2})(\d{2})/) : null;
            const topicDate = dateMatch ? `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}` : null;
            businessOppoTopics.push({
                text,
                topic,
                topicId: topicId || null,
                topicDate,
                categoryId: parseUrlParam(url, 'leafcate_pre'),
                url: url || null,
            });
        }
        else if (matKey === 'price_competitive' || /近\d+天低价|比同款低/.test(text)) {
            priceCompetitiveBadges.push(text);
        }
    }
    const soldCountText = d?.afterPrice?.text ?? d?.afterPriceList?.[0]?.text ?? null;
    const soldCountTotal = parseCountText(soldCountText);
    const tradeScoreRaw = d?.shopAddition?.tradeService?.compositeNewScore;
    const tradeScore = tradeScoreRaw ? parseFloat(tradeScoreRaw) : null;
    return {
        newProductSellPoints,
        rankBadges,
        businessOppoTopics,
        priceCompetitiveBadges,
        soldCountText,
        soldCountTotal,
        kuaJingPuHuo: bool(d?.kuaJingPuHuo),
        fenxiaoNewOffer: bool(d?.shopAddition?.fenxiaoNewOffer),
        tradeScore: Number.isFinite(tradeScore) ? tradeScore : null,
    };
}
export function mapOffer(item) {
    const d = item.data;
    if (!d?.offerId)
        return null;
    const title = (d.title ?? '').replace(/<\/?font[^>]*>/g, '').trim();
    const priceRaw = d.priceInfo?.price;
    const price = priceRaw ? parseFloat(priceRaw) : null;
    const yearsRaw = d.shop?.tpYear;
    const years = yearsRaw ? parseInt(yearsRaw, 10) : null;
    const tags = (d.tags ?? [])
        .map((t) => t?.text?.trim() ?? '')
        .filter((s) => !!s);
    const serviceTags = textList(d.serviceTags);
    const productBadges = textList(d.productBadges);
    const orderCountText = d.orderCountText ??
        (typeof d.orderCount === 'string' ? d.orderCount : undefined) ??
        d.bookedCount ??
        null;
    const repurchaseRateText = d.repurchaseRateText ??
        d.repurchaseRate ??
        d.turnHead?.percent ??
        (d.afterTags?.matKey === 'return_rate' ? d.afterTags?.text : undefined) ??
        d.offerRepurchaseRate ??
        null;
    const trendSignals = extractTrendSignals(d);
    return {
        offerId: d.offerId,
        title,
        price: {
            text: priceRaw ? `¥${priceRaw}` : '',
            min: price,
            max: price,
        },
        supplier: {
            name: d.shop?.text ?? null,
            shopUrl: d.shopAddition?.shopLinkUrl ?? d.winPortUrl ?? null,
            years,
        },
        location: {
            province: d.province ?? null,
            city: d.city ?? null,
        },
        bizType: d.bizType ?? null,
        verified: {
            factory: bool(d.factoryInspection),
            business: bool(d.businessInspection),
            superFactory: bool(d.superFactory),
        },
        tags,
        ...(serviceTags.length ? { serviceTags } : {}),
        ...(productBadges.length ? { productBadges } : {}),
        demand: {
            orderCountText,
            orderCount: typeof d.orderCount === 'number'
                ? d.orderCount
                : parseCountText(orderCountText),
            repurchaseRateText,
            repurchaseRate: parsePercentText(repurchaseRateText),
        },
        trendSignals,
        isP4P: bool(d.isP4P),
        turnover: d.bookedCount ?? null,
        url: `https://detail.1688.com/offer/${d.offerId}.html`,
        image: d.offerPicUrl ?? null,
    };
}
export function readSearchMtopRequestMeta(url) {
    if (!url.includes(SEARCH_MTOP_API))
        return null;
    try {
        const dataParam = new URLSearchParams(new URL(url).search).get('data') ?? '';
        if (!dataParam)
            return null;
        const dataObj = JSON.parse(dataParam);
        const params = JSON.parse(dataObj.params ?? '{}');
        const beginPage = params.beginPage === undefined ? undefined : Number(params.beginPage);
        return {
            appId: String(dataObj.appId),
            method: params.method,
            beginPage,
            sortType: params.sortType,
        };
    }
    catch {
        return null;
    }
}
export function parseOfferItemsFromMtopText(text) {
    const json = parseMtopJsonp(text);
    const items = json?.data?.data?.OFFER?.items ?? [];
    return items.map(mapOffer).filter((o) => o !== null);
}
//# sourceMappingURL=search-mtop.js.map
