import { Routes, RouterModule } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { NgModule } from '@angular/core';
import { TypeSelectorComponent } from './upload/type-selector/type-selector.component';
import { PropertyBuilderComponent } from './upload/property-builder/property-builder.component';
import { DimensionBuilderComponent } from './upload/dimension-builder/dimension-builder.component';
import { AuthGuardService } from 'src/app/shared/services/auth-guard.service';
import { LoadComponent } from './upload/load/load.component';

const routes: Routes = [
    {path: 'upload', component: UploadComponent, canActivate: [AuthGuardService], children: [
        {path: '', redirectTo: 'type', pathMatch: 'full'},
        {path: 'type', component: TypeSelectorComponent},
        {path: 'properties', component: PropertyBuilderComponent},
        {path: 'dimensions', component: DimensionBuilderComponent},
        {path: 'load', component: LoadComponent}
    ]}
];

@NgModule({
    declarations: [],
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class UploadRoutingModule {  }
