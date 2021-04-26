export interface User {
    readonly username: string;
    readonly email: string;
    readonly user_level: number;
    readonly allowed_upload_types?: string[] | string;
}