import { Routes, RouterModule } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { NgModule } from '@angular/core';
import { TypeSelectorComponent } from './upload/type-selector/type-selector.component';
import { PropertyBuilderComponent } from './upload/property-builder/property-builder.component';

const routes: Routes = [
    {path: 'upload', component: UploadComponent, children: [
        {path: '', redirectTo: 'type', pathMatch: 'full'},
        {path: 'type', component: TypeSelectorComponent},
        {path: 'properties', component: PropertyBuilderComponent}
    ]}
];

@NgModule({
    declarations: [],
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class UploadRoutingModule {  }
