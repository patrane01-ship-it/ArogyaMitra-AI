import crypto from 'crypto';
import { InvalidParameterValueError } from '../exceptions/arogya_errors.ts';

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export interface ContributingFactor {
  param_name: string;
  value: number;
  weight: number;
  contribution: number;
  status: string;
}

export class RiskScore {
  score_id: string;
  user_id: string;
  computed_at: Date;
  overall_risk: number;
  risk_level: RiskLevel;
  contributing_factors: ContributingFactor[];
  recommendations: string[];
  version: number;

  constructor(params: {
    score_id?: string;
    user_id?: string;
    computed_at?: Date;
    overall_risk: number;
    risk_level?: RiskLevel;
    contributing_factors?: ContributingFactor[];
    recommendations?: string[];
    version?: number;
  }) {
    this.score_id = params.score_id || globalThis.crypto?.randomUUID() || crypto.randomUUID();
    this.user_id = params.user_id || 'local_user';
    this.computed_at = params.computed_at || new Date();
    this.overall_risk = Math.max(0.0, Math.min(1.0, params.overall_risk));
    this.contributing_factors = params.contributing_factors || [];
    this.recommendations = params.recommendations || [];
    this.version = params.version || 1;
    this.risk_level = params.risk_level || this.computeRiskLevel();
  }

  computeRiskLevel(): RiskLevel {
    const risk = this.overall_risk;
    if (risk < 0.30) {
      return 'LOW';
    } else if (risk < 0.60) {
      return 'MODERATE';
    } else if (risk < 0.80) {
      return 'HIGH';
    } else {
      return 'CRITICAL';
    }
  }

  validate(): void {
    if (typeof this.overall_risk !== 'number' || isNaN(this.overall_risk) || this.overall_risk < 0.0 || this.overall_risk > 1.0) {
      throw new InvalidParameterValueError(`overall_risk must be a float between 0.0 and 1.0. Got: ${this.overall_risk}`);
    }
    
    if (!Array.isArray(this.contributing_factors)) {
      throw new InvalidParameterValueError('contributing_factors must be an array');
    }

    if (this.contributing_factors.length === 0) {
      throw new InvalidParameterValueError('contributing_factors list cannot be empty');
    }

    if (!Array.isArray(this.recommendations)) {
      throw new InvalidParameterValueError('recommendations must be an array');
    }

    // Recalculate level to be sure
    this.risk_level = this.computeRiskLevel();
  }

  toDict(): Record<string, any> {
    return {
      score_id: this.score_id,
      user_id: this.user_id,
      computed_at: this.computed_at.toISOString(),
      overall_risk: this.overall_risk,
      risk_level: this.risk_level,
      contributing_factors: this.contributing_factors,
      recommendations: this.recommendations,
      version: this.version
    };
  }

  static fromDict(data: Record<string, any>): RiskScore {
    return new RiskScore({
      score_id: data.score_id,
      user_id: data.user_id,
      computed_at: new Date(data.computed_at),
      overall_risk: Number(data.overall_risk),
      risk_level: data.risk_level as RiskLevel,
      contributing_factors: typeof data.contributing_factors === 'string'
        ? JSON.parse(data.contributing_factors)
        : data.contributing_factors || [],
      recommendations: typeof data.recommendations === 'string'
        ? JSON.parse(data.recommendations)
        : data.recommendations || [],
      version: Number(data.version)
    });
  }
}
