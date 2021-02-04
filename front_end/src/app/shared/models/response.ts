export interface Response<T> {
    results?: T[];
    result?: T;
    error: string;
    status: string;
}